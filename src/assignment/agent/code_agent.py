"""The Part 1 coding agent: fix a software issue and submit a git patch."""

from __future__ import annotations

import json
from typing import Any

from assignment.agent.base import (
    DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
    DEFAULT_COMPACTION_MAX_TOKENS,
    Agent,
)
from assignment.agent.tools import EXECUTE_TOOL, SEND_MESSAGE_TOOL
from assignment.env import Environment

SYSTEM_PROMPT_TEMPLATE = """
<system_information>
{
  "machine": <machine>,
  "release": <release>,
  "system": <system>,
  "version": <version>
}
</system_information>
"""

class CodeAgent(Agent):
    """An agent that fixes a software issue and submits a git patch."""

    def __init__(
        self,
        task: str,
        environment: Environment,
        model: str | None = None,
        logs_save_path: str | None = None,
        step_limit: int = 100,
        skills_path: str | None = None,
        auto_stop_environment: bool = True,
        compact_threshold_tokens: int | None = None,
        compaction_keep_recent_steps: int = DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
        compaction_max_tokens: int = DEFAULT_COMPACTION_MAX_TOKENS,
    ):
        super().__init__(
            environment=environment,
            model=model,
            logs_save_path=logs_save_path,
            step_limit=step_limit,
            skills_path=skills_path,
            auto_stop_environment=auto_stop_environment,
            compact_threshold_tokens=compact_threshold_tokens,
            compaction_keep_recent_steps=compaction_keep_recent_steps,
            compaction_max_tokens=compaction_max_tokens,
        )
        self.task = task
        self.submitted_patch = ""

        # TODO(Part 1.3): Make the `execute` and `send_message` tools available
        # to the agent.
        self.tools.extend([EXECUTE_TOOL, SEND_MESSAGE_TOOL])

        # TODO(1.1.b): Construct the system prompt and task_prompt. These
        # should be usable by the `Agent.build_prompt` method.
        self.system_prompt = SYSTEM_PROMPT_TEMPLATE\
            .replace("<machine>", environment.machine)\
            .replace("<release>", environment.release)\
            .replace("<system>", environment.system)\
            .replace("<version>", environment.version)
        self.task_prompt = task
        # TODO(1.4): If any skills are available to the agent, make their
        # descriptions/metadata available to the agent in the prompt.

    def execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Execute ``execute`` and ``send_message`` calls in the code sandbox."""

        # TODO(Part 1.3): Parse each call, execute recognized tools, and return
        # one message per call (there may be multiple tool calls in one agent
        # response!). Malformed JSON and unknown tools must become recoverable
        # observations relayed to the agent instead of exceptions.
        
        # uv run pytest -s tests/test_agent.py -k test_prompt_carries_task_action_and_result
        # print(json.dumps(tool_calls, indent=2), flush=True)
        '''
        tool call result schema:
        {
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": "..."
        }
        '''
        tool_call_results = []
        for tc in tool_calls:
            result = {}
            if tc.get("type") != "function":
                result = {
                    'role': "tool",
                    'tool_call_id': tc.get("id"),
                    'content': "Error: tool call type is not 'function'."
                }
                tool_call_results.append(result)
                continue
            func = tc.get("function", {})
            name = func.get("name")
            try:
                args = json.loads(func.get("arguments", {}))
                command = args.get("command")
                shell = args.get("shell", True)
                cwd = args.get("cwd")
                timeout = args.get("timeout")
                env = args.get("env")
            except Exception as e:
                result = {
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": f"Error parsing tool call arguments: {str(e)}"
                }
                tool_call_results.append(result)
                continue
            if name == "execute":
                try:
                    obs = self.env.execute(
                        command=command,
                        shell=shell,
                        cwd=cwd,
                        timeout=timeout,
                        env=env,
                    )
                    result = {
                        "role": "tool",
                        "tool_call_id": tc.get("id"),
                        "content": json.dumps(obs)
                    }
                    tool_call_results.append(result)
                except Exception as e:
                    result = {
                        "role": "tool",
                        "tool_call_id": tc.get("id"),
                        "content": str(e)
                    }
                    tool_call_results.append(result)
            elif name == "send_message":
                summary = args.get("summary")
                # For send_message, we just return the message as an observation.
                result = {
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": f"Message sent: {summary}"
                }
                tool_call_results.append(result)
            else:
                result = {
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "content": f"Unknown tool: {name}"
                }
                tool_call_results.append(result)
        return tool_call_results