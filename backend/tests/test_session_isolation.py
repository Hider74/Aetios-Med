"""
Test session isolation for agent orchestrators.
"""
import pytest
from unittest.mock import Mock, AsyncMock, MagicMock


def test_session_isolation_logic():
    """Test that session isolation logic creates separate agents per session."""
    # Simulate the app.state structure
    class AppState:
        def __init__(self):
            self.agent_sessions = {}
            self.create_agent = Mock(side_effect=lambda: Mock(id=len(self.agent_sessions)))
    
    app_state = AppState()
    
    # Simulate first request with session "alice"
    session_id_1 = "alice"
    if session_id_1 not in app_state.agent_sessions:
        app_state.agent_sessions[session_id_1] = app_state.create_agent()
    agent_1 = app_state.agent_sessions[session_id_1]
    
    # Simulate second request with session "bob"
    session_id_2 = "bob"
    if session_id_2 not in app_state.agent_sessions:
        app_state.agent_sessions[session_id_2] = app_state.create_agent()
    agent_2 = app_state.agent_sessions[session_id_2]
    
    # Simulate third request with session "alice" again
    session_id_3 = "alice"
    if session_id_3 not in app_state.agent_sessions:
        app_state.agent_sessions[session_id_3] = app_state.create_agent()
    agent_3 = app_state.agent_sessions[session_id_3]
    
    # Verify that alice reuses the same agent
    assert agent_1 is agent_3, "Same session should reuse the same agent"
    
    # Verify that bob has a different agent
    assert agent_1 is not agent_2, "Different sessions should have different agents"
    
    # Verify we only created 2 agents (not 3)
    assert len(app_state.agent_sessions) == 2
    assert app_state.create_agent.call_count == 2


def test_session_cleanup_on_delete():
    """Test that deleting chat history removes the agent from sessions."""
    # Simulate the app.state structure
    class AppState:
        def __init__(self):
            self.agent_sessions = {"alice": Mock(), "bob": Mock()}
    
    app_state = AppState()
    
    # Simulate DELETE /history for alice
    session_id = "alice"
    if session_id in app_state.agent_sessions:
        del app_state.agent_sessions[session_id]
    
    # Verify alice's agent was removed
    assert "alice" not in app_state.agent_sessions
    
    # Verify bob's agent is still there
    assert "bob" in app_state.agent_sessions


def test_max_sessions_limit():
    """Test that the max sessions limit prevents unbounded growth."""
    # Simulate the app.state structure
    class AppState:
        def __init__(self):
            self.agent_sessions = {}
            self.create_agent = Mock(side_effect=lambda: Mock(id=len(self.agent_sessions)))
    
    app_state = AppState()
    MAX_SESSIONS = 20
    
    # Create 25 sessions
    for i in range(25):
        session_id = f"session_{i}"
        if session_id not in app_state.agent_sessions:
            app_state.agent_sessions[session_id] = app_state.create_agent()
            if len(app_state.agent_sessions) > MAX_SESSIONS:
                # Remove oldest session (first inserted)
                oldest_key = next(iter(app_state.agent_sessions))
                del app_state.agent_sessions[oldest_key]
    
    # Verify we never exceed MAX_SESSIONS
    assert len(app_state.agent_sessions) == MAX_SESSIONS
    
    # Verify the oldest sessions were removed (session_0 through session_4)
    assert "session_0" not in app_state.agent_sessions
    assert "session_4" not in app_state.agent_sessions
    
    # Verify the newest sessions are still there
    assert "session_24" in app_state.agent_sessions
    assert "session_20" in app_state.agent_sessions


if __name__ == "__main__":
    test_session_isolation_logic()
    test_session_cleanup_on_delete()
    test_max_sessions_limit()
    print("✓ All session isolation tests passed")
