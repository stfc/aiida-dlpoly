"""Tests for the aiida-mcp integration module, aiida_dlpoly.mcp.

Requires the optional ``mcp`` extra (``pip install -e .[mcp]``), which installs
aiida-mcp and the ``mcp`` SDK; skipped entirely if that extra is not installed (e.g.
in CI jobs that only install the base package).
"""

import asyncio
import uuid
from unittest import mock

import pytest

pytest.importorskip("aiida_mcp")

from aiida import orm  # noqa: E402
from aiida_mcp.plugins import calcjob  # noqa: E402
from aiida_mcp.plugins.inputs import ControlInput, FileInput  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

from aiida_dlpoly import mcp as dlpoly_mcp  # noqa: E402


def _tool_names(server: MCPServer) -> set[str]:
    return {tool.name for tool in asyncio.run(server.list_tools())}


@pytest.fixture
def code(aiida_localhost):
    """Return a stored DL_POLY code on the test computer."""
    return orm.InstalledCode(
        label=f"dlpoly-test-{uuid.uuid4().hex[:8]}",
        computer=aiida_localhost,
        filepath_executable="/bin/true",
        default_calc_job_plugin="dlpoly",
    ).store()


@pytest.fixture
def fake_submit():
    """Replace the daemon submit with a stub that returns a process-like node."""
    node = orm.CalcJobNode()
    node.set_process_type("aiida.calculations:dlpoly")
    with mock.patch.object(calcjob, "submit", return_value=node) as patched:
        node.store_all = lambda: None
        yield patched


@pytest.fixture
def stored_node_returned(fake_submit):
    """Make the fake submit return an already-stored CalcJobNode."""
    fake_submit.return_value = orm.CalcJobNode().store()
    return fake_submit


def _files(tmp_path):
    config = tmp_path / "CONFIG"
    field = tmp_path / "FIELD"
    config.write_text("config text\n")
    field.write_text("field text\n")
    return config, field


def test_is_available():
    """is_available reflects whether the dlpoly calcjob entry point is installed."""
    assert dlpoly_mcp.is_available() is True


def test_describe_dlpoly_inputs():
    """describe_calcjob reports the DL_POLY-specific inputs."""
    description = calcjob.describe_calcjob("dlpoly")
    inputs = {port["name"]: port for port in description["inputs"]}

    assert set(inputs) == {"code", "configuration", "field", "control"}
    assert inputs["field"]["required"] is True
    assert inputs["field"]["types"] == ["SinglefileData"]
    assert inputs["control"]["types"] == ["SinglefileData", "Dict"]
    assert inputs["code"]["required"] is False


def test_describe_dlpoly_outputs_exclude_base_calcjob_outputs():
    """describe_calcjob excludes outputs inherited from the base CalcJob."""
    description = calcjob.describe_calcjob("dlpoly")
    outputs = {port["name"]: port for port in description["outputs"]}

    expected = {"output", "statistics", "revive_configuration", "rdf", "history"}
    assert set(outputs) == expected
    assert outputs["output"]["required"] is True
    assert outputs["rdf"]["required"] is False
    assert "retrieved" not in outputs


def test_describe_dlpoly_exit_codes():
    """describe_calcjob reports the DL_POLY-specific exit codes."""
    description = calcjob.describe_calcjob("dlpoly")
    statuses = {code["status"]: code["name"] for code in description["exit_codes"]}

    assert statuses[300] == "ERROR_OUTPUT_NOT_FOUND"
    assert sorted(statuses) == [300, 301, 302, 303, 304, 305]


def test_describe_dlpoly_option_defaults():
    """describe_calcjob reports the metadata option defaults the plugin changed."""
    defaults = calcjob.describe_calcjob("dlpoly")["metadata_option_defaults"]

    assert defaults["parser_name"] == "dlpoly"
    assert defaults["resources"] == {"num_machines": 1, "num_mpiprocs_per_machine": 1}


def test_register_adds_tool():
    """register() adds the DL_POLY describe and submit tools."""
    server = MCPServer("test")
    dlpoly_mcp.register(server)
    assert _tool_names(server) == {"describe_dlpoly_calcjob", "submit_dlpoly_job"}


def test_submit_job_builds_validated_inputs(code, tmp_path, stored_node_returned):
    """submit_job builds, stores and submits validated inputs."""
    config, field = _files(tmp_path)
    result = dlpoly_mcp.submit_job(
        code=code.pk,
        configuration=FileInput(path=str(config)),
        field=FileInput(path=str(field)),
        control=ControlInput(parameters={"temperature": [500, "K"]}),
        num_machines=2,
        num_mpiprocs_per_machine=4,
    )

    stored_node_returned.assert_called_once()
    submitted = stored_node_returned.call_args.kwargs
    assert submitted["code"].pk == code.pk
    resources = submitted["metadata"]["options"]["resources"]
    assert resources == {"num_machines": 2, "num_mpiprocs_per_machine": 4}
    assert submitted["configuration"].is_stored
    assert submitted["field"].is_stored
    assert submitted["control"].is_stored

    assert result["pk"] == stored_node_returned.return_value.pk
    assert set(result["inputs"]) == {"configuration", "field", "control"}
    assert result["code"] == code.full_label


def test_submit_job_sets_label_and_description(code, tmp_path, stored_node_returned):
    """submit_job passes label and description through to the calcjob metadata."""
    config, field = _files(tmp_path)
    dlpoly_mcp.submit_job(
        code=code.pk,
        configuration=FileInput(path=str(config)),
        field=FileInput(path=str(field)),
        control=ControlInput(parameters={}),
        label="my run",
        description="a test run",
    )

    metadata = stored_node_returned.call_args.kwargs["metadata"]
    assert metadata["label"] == "my run"
    assert metadata["description"] == "a test run"


def test_submit_job_omits_label_and_description_by_default(
    code, tmp_path, stored_node_returned
):
    """submit_job omits label and description from metadata when not given."""
    config, field = _files(tmp_path)
    dlpoly_mcp.submit_job(
        code=code.pk,
        configuration=FileInput(path=str(config)),
        field=FileInput(path=str(field)),
        control=ControlInput(parameters={}),
    )

    metadata = stored_node_returned.call_args.kwargs["metadata"]
    assert "label" not in metadata
    assert "description" not in metadata


def test_submit_job_accepts_code_label(code, tmp_path, stored_node_returned):
    """submit_job accepts a code's full label as well as its PK."""
    config, field = _files(tmp_path)
    dlpoly_mcp.submit_job(
        code=code.full_label,
        configuration=FileInput(path=str(config)),
        field=FileInput(path=str(field)),
        control=ControlInput(text="title t\n"),
    )

    assert stored_node_returned.call_args.kwargs["code"].pk == code.pk


def test_submit_job_unknown_code_creates_nothing(tmp_path, fake_submit):
    """An unknown code is a ToolError and creates no nodes."""
    config, field = _files(tmp_path)
    before = orm.QueryBuilder().append(orm.Node).count()

    with pytest.raises(ToolError, match="No code found"):
        dlpoly_mcp.submit_job(
            code="nope@nowhere",
            configuration=FileInput(path=str(config)),
            field=FileInput(path=str(field)),
            control=ControlInput(parameters={}),
        )

    fake_submit.assert_not_called()
    assert orm.QueryBuilder().append(orm.Node).count() == before


def test_submit_job_invalid_inputs_store_nothing(code, tmp_path, fake_submit):
    """Invalid inputs are a ToolError and store no new nodes."""
    config, field = _files(tmp_path)
    before = orm.QueryBuilder().append(orm.Node).count()
    wrong = orm.Int(1).store()
    after_setup = before + 1

    with pytest.raises(ToolError, match="expected SinglefileData, Dict"):
        dlpoly_mcp.submit_job(
            code=code.pk,
            configuration=FileInput(path=str(config)),
            field=FileInput(path=str(field)),
            control=ControlInput(pk=wrong.pk),
        )

    fake_submit.assert_not_called()
    assert orm.QueryBuilder().append(orm.Node).count() == after_setup


def test_submit_job_rejects_bad_resources(code, tmp_path, fake_submit):
    """A resources value below 1 is a ToolError."""
    config, field = _files(tmp_path)
    with pytest.raises(ToolError, match="num_machines must be at least 1"):
        dlpoly_mcp.submit_job(
            code=code.pk,
            configuration=FileInput(path=str(config)),
            field=FileInput(path=str(field)),
            control=ControlInput(parameters={}),
            num_machines=0,
        )
    fake_submit.assert_not_called()


def test_submit_calcjob_validates_before_storing(aiida_profile, fake_submit):
    """submit_calcjob validates inputs before storing any of them."""
    unstored = orm.SinglefileData(content="x", filename="FIELD")

    with pytest.raises(ToolError, match="Invalid inputs for dlpoly"):
        calcjob.submit_calcjob("dlpoly", {"field": unstored})

    assert not unstored.is_stored
    fake_submit.assert_not_called()


def test_submit_tool_is_registered_with_input_schema():
    """submit_dlpoly_job is registered with the expected input schema."""
    server = MCPServer("test")
    dlpoly_mcp.register(server)
    tools = {tool.name: tool for tool in asyncio.run(server.list_tools())}

    schema = tools["submit_dlpoly_job"].input_schema
    assert set(schema["required"]) == {"code", "configuration", "field", "control"}
    assert {"label", "description"} <= set(schema["properties"])
    assert {"path", "text", "pk"} <= set(schema["$defs"]["FileInput"]["properties"])
    assert "parameters" in schema["$defs"]["ControlInput"]["properties"]
