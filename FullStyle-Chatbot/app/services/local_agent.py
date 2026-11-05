"""Deterministic local adapter exercising real authorization and business requests."""

import json

from app.infrastructure.clients.business_logic_client import BusinessLogicClient


class LocalAgent:
    async def generate_text_with_agent(self, user_input, session_id, history=None):
        if user_input.strip() == "historial":
            return json.dumps(history or [], ensure_ascii=False)
        client = BusinessLogicClient()
        command = user_input.strip().split()
        if command == ["mis", "citas"]:
            response = await client.request_with_retry("GET", client.base_url + "/appointment")
            return json.dumps(response.json(), ensure_ascii=False)
        if len(command) == 2 and command[0] == "cancelar" and command[1].isdecimal():
            result = await client.delete_appointment(int(command[1]))
            return json.dumps(result, ensure_ascii=False)
        return "Adaptador local: usa 'mis citas' o 'cancelar <id>'. No hay proveedor LLM conectado."


local_agent = LocalAgent()
