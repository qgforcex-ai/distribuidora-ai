import json
import os

from google import genai
from google.genai import types

from app.ai.providers.base import LLMProvider


class GeminiProvider(LLMProvider):

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não configurada."
            )

        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-3.5-flash"
        )

        self.client = genai.Client(
            api_key=self.api_key
        )

    def chat(self, messages, tools=None):
        contents, system_instruction = self._convert_messages(
            messages
        )

        config_args = {}

        if system_instruction:
            config_args["system_instruction"] = system_instruction

        gemini_tools = self._convert_tools(tools)
        if gemini_tools:
            config_args["tools"] = gemini_tools
            config_args["automatic_function_calling"] = (
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            )

        config = (
            types.GenerateContentConfig(**config_args)
            if config_args
            else None
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=config
        )

        return self._convert_response(response)

    def _convert_messages(self, messages):
        contents = []
        system_parts = []
        pending_tool_names = []

        for message in messages:
            role = message.get("role")
            content = message.get("content") or ""

            if role == "system":
                system_parts.append(content)
                continue

            if role == "assistant":
                tool_calls = message.get("tool_calls") or []
                if tool_calls:
                    parts = []
                    for tool_call in tool_calls:
                        function = tool_call.get("function", {})
                        name = function.get("name")
                        arguments = function.get("arguments", {})
                        if isinstance(arguments, str):
                            arguments = json.loads(arguments)
                        if name:
                            pending_tool_names.append(name)
                            parts.append(
                                types.Part.from_function_call(
                                    name=name,
                                    args=arguments
                                )
                            )
                    if parts:
                        contents.append(
                            types.Content(
                                role="model",
                                parts=parts
                            )
                        )
                        continue

                contents.append(
                    types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=content)]
                    )
                )
                continue

            if role == "tool":
                name = message.get("name")
                if not name and pending_tool_names:
                    name = pending_tool_names.pop(0)
                if not name:
                    name = "tool"

                try:
                    response_content = json.loads(content)
                except json.JSONDecodeError:
                    response_content = {"result": content}

                contents.append(
                    types.Content(
                        role="tool",
                        parts=[
                            types.Part.from_function_response(
                                name=name,
                                response=response_content
                            )
                        ]
                    )
                )
                continue

            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=content)]
                )
            )

        return contents, "\n\n".join(system_parts)

    def _convert_tools(self, tools):
        if not tools:
            return None

        function_declarations = []

        for tool in tools:
            if tool.get("type") != "function":
                continue

            function = tool.get("function", {})
            name = function.get("name")
            if not name:
                continue

            function_declarations.append(
                types.FunctionDeclaration(
                    name=name,
                    description=function.get("description", ""),
                    parameters_json_schema=function.get(
                        "parameters",
                        {}
                    )
                )
            )

        if not function_declarations:
            return None

        return [
            types.Tool(
                function_declarations=function_declarations
            )
        ]

    def _convert_response(self, response):
        tool_calls = []

        for function_call in response.function_calls or []:
            tool_calls.append(
                {
                    "type": "function",
                    "function": {
                        "name": function_call.name,
                        "arguments": dict(function_call.args or {})
                    }
                }
            )

        return {
            "role": "assistant",
            "content": self._response_text(response),
            "tool_calls": tool_calls
        }

    def _response_text(self, response):
        try:
            return response.text or ""
        except ValueError:
            return ""
