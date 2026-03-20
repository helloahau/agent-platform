"""Streamlit dashboard for the Agent Platform."""

from __future__ import annotations

import requests
import streamlit as st

API_BASE = "http://localhost:8000/api"

st.set_page_config(page_title="Agent Platform", page_icon="🤖", layout="wide")


def api_get(path: str):
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
        return None


def api_post(path: str, data: dict):
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, timeout=120)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
        return None


def api_delete(path: str):
    try:
        r = requests.delete(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return True
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
        return False


# ── Sidebar ──────────────────────────────────────────────────────────────────

st.sidebar.title("Agent Platform")
page = st.sidebar.radio("Navigate", ["Chat", "Agents", "Create Agent", "Tools"])

# ── Chat Page ────────────────────────────────────────────────────────────────

if page == "Chat":
    st.title("Chat with an Agent")

    agents = api_get("/agents/")
    if not agents:
        st.info("No agents available. Create one first.")
    else:
        agent_names = [a["name"] for a in agents]
        selected = st.selectbox("Select Agent", agent_names)

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        if "session_id" not in st.session_state:
            st.session_state.session_id = None

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Type your message..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = api_post(
                        f"/chat/{selected}",
                        {
                            "message": prompt,
                            "session_id": st.session_state.session_id,
                        },
                    )
                if result:
                    st.session_state.session_id = result.get("session_id")
                    reply = result.get("response", "")
                    st.markdown(reply)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": reply}
                    )
                else:
                    st.error("Failed to get a response.")

        if st.sidebar.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.session_id = None
            st.rerun()

# ── Agents Page ──────────────────────────────────────────────────────────────

elif page == "Agents":
    st.title("Registered Agents")

    agents = api_get("/agents/")
    if not agents:
        st.info("No agents registered yet.")
    else:
        for agent in agents:
            with st.expander(f"**{agent['name']}** — {agent['description']}"):
                st.markdown(f"**Model:** `{agent.get('model') or 'default'}`")
                st.markdown(f"**Temperature:** {agent['temperature']}")
                st.markdown(f"**Tools:** {', '.join(agent['tools']) or 'none'}")
                st.markdown(f"**Max Iterations:** {agent['max_iterations']}")
                st.markdown(f"**Memory:** {agent['memory_type']}")
                st.code(agent["system_prompt"], language="text")

                if st.button(f"Delete {agent['name']}", key=f"del_{agent['name']}"):
                    if api_delete(f"/agents/{agent['name']}"):
                        st.success(f"Deleted '{agent['name']}'.")
                        st.rerun()

# ── Create Agent Page ────────────────────────────────────────────────────────

elif page == "Create Agent":
    st.title("Create a New Agent")

    tools_data = api_get("/tools/") or []
    available_tools = [t["name"] for t in tools_data]

    with st.form("create_agent_form"):
        name = st.text_input("Agent Name", placeholder="my-agent")
        description = st.text_area("Description", placeholder="What does this agent do?")
        system_prompt = st.text_area(
            "System Prompt",
            value="You are a helpful AI assistant.",
            height=150,
        )
        temperature = st.slider("Temperature", 0.0, 2.0, 0.0, 0.1)
        max_iterations = st.number_input("Max Iterations", 1, 50, 10)
        selected_tools = st.multiselect("Tools", available_tools)
        memory_type = st.selectbox("Memory Type", ["conversation", "persistent"])

        submitted = st.form_submit_button("Create Agent")
        if submitted:
            if not name:
                st.error("Agent name is required.")
            else:
                payload = {
                    "name": name,
                    "description": description,
                    "system_prompt": system_prompt,
                    "temperature": temperature,
                    "max_iterations": max_iterations,
                    "tools": selected_tools,
                    "memory_type": memory_type,
                }
                result = api_post("/agents/", payload)
                if result:
                    st.success(f"Agent '{name}' created successfully!")

# ── Tools Page ───────────────────────────────────────────────────────────────

elif page == "Tools":
    st.title("Available Tools")

    tools_data = api_get("/tools/")
    if not tools_data:
        st.info("No tools registered.")
    else:
        for tool in tools_data:
            with st.expander(f"**{tool['name']}** — {tool['description']}"):
                st.json(tool["parameters"])
