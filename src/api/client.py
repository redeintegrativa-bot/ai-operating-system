#!/usr/bin/env python3
"""Python client library for the AI Operating System REST API."""

from __future__ import annotations

import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import httpx


class AIOSClientError(Exception):
    """Base exception for AI OS API client errors."""


class AIOSClient:
    """Client for the AI Operating System REST API.

    Usage:
        client = AIOSClient("http://localhost:8000")
        tasks = client.list_tasks()
        task = client.create_task("Build the thing", priority="high")
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    def close(self):
        self._client.close()

    def __enter__(self) -> AIOSClient:
        return self

    def __exit__(self, *args):
        self.close()

    # ------------------------------------------------------------------
    # Request helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"/api{path}"
        try:
            resp = self._client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            detail = self._extract_error(e.response)
            raise AIOSClientError(f"{e.response.status_code}: {detail}") from e
        except httpx.RequestError as e:
            raise AIOSClientError(f"Request failed: {e}") from e

    def _extract_error(self, response: httpx.Response) -> str:
        try:
            body = response.json()
            return body.get("detail", body.get("message", str(body)))
        except (json.JSONDecodeError, AttributeError):
            return response.text or str(response.status_code)

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    def create_task(
        self,
        description: str,
        priority: str = "medium",
        metadata: Optional[Dict] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict:
        """Create a new task."""
        body: Dict = {"description": description, "priority": priority}
        if metadata:
            body["metadata"] = metadata
        if timeout_seconds is not None:
            body["timeout_seconds"] = timeout_seconds
        return self._request("POST", "/tasks", json=body)

    def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict:
        """List all tasks, optionally filtered by status."""
        params: Dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return self._request("GET", "/tasks", params=params)

    def get_task(self, task_id: str) -> Dict:
        """Get a single task by ID."""
        return self._request("GET", f"/tasks/{task_id}")

    def update_task(
        self,
        task_id: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Update a task."""
        body: Dict = {}
        if description is not None:
            body["description"] = description
        if priority is not None:
            body["priority"] = priority
        if status is not None:
            body["status"] = status
        if metadata is not None:
            body["metadata"] = metadata
        return self._request("PUT", f"/tasks/{task_id}", json=body)

    def delete_task(self, task_id: str) -> Dict:
        """Delete a task."""
        return self._request("DELETE", f"/tasks/{task_id}")

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    def list_agents(self) -> List[Dict]:
        """List all available agents."""
        return self._request("GET", "/agents")

    def get_agent(self, agent_name: str) -> Dict:
        """Get details for a specific agent."""
        return self._request("GET", f"/agents/{agent_name}")

    def execute_task_on_agent(self, agent_name: str, task: str) -> Dict:
        """Execute a task on a specific agent."""
        return self._request("POST", f"/agents/{agent_name}/execute", json={"task": task})

    # ------------------------------------------------------------------
    # System
    # ------------------------------------------------------------------

    def get_status(self) -> Dict:
        """Get system status."""
        return self._request("GET", "/status")

    def get_metrics(self) -> Dict:
        """Get system metrics."""
        return self._request("GET", "/metrics")

    def health_check(self) -> Dict:
        """Check if the API server is healthy."""
        return self._request("GET", "/health")

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def get_memories(
        self,
        agent: str,
        memory_type: Optional[str] = None,
    ) -> List[Dict]:
        """Get memories for an agent."""
        params = {}
        if memory_type:
            params["memory_type"] = memory_type
        return self._request("GET", f"/memory/{agent}", params=params)

    def add_memory(
        self,
        agent: str,
        content: Dict,
        memory_type: str = "episodic",
        keywords: Optional[List[str]] = None,
        importance: float = 0.5,
    ) -> Dict:
        """Add a memory for an agent."""
        body = {
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
        }
        if keywords:
            body["keywords"] = keywords
        return self._request("POST", f"/memory/{agent}", json=body)


class AsyncAIOSClient:
    """Async client for the AI Operating System REST API.

    Usage:
        async with AsyncAIOSClient("http://localhost:8000") as client:
            tasks = await client.list_tasks()
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def close(self):
        await self._client.aclose()

    async def __aenter__(self) -> AsyncAIOSClient:
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"/api{path}"
        try:
            resp = await self._client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            detail = self._extract_error(e.response)
            raise AIOSClientError(f"{e.response.status_code}: {detail}") from e
        except httpx.RequestError as e:
            raise AIOSClientError(f"Request failed: {e}") from e

    def _extract_error(self, response: httpx.Response) -> str:
        try:
            body = response.json()
            return body.get("detail", body.get("message", str(body)))
        except (json.JSONDecodeError, AttributeError):
            return response.text or str(response.status_code)

    async def create_task(
        self,
        description: str,
        priority: str = "medium",
        metadata: Optional[Dict] = None,
        timeout_seconds: Optional[int] = None,
    ) -> Dict:
        body: Dict = {"description": description, "priority": priority}
        if metadata:
            body["metadata"] = metadata
        if timeout_seconds is not None:
            body["timeout_seconds"] = timeout_seconds
        return await self._request("POST", "/tasks", json=body)

    async def list_tasks(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict:
        params: Dict = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        return await self._request("GET", "/tasks", params=params)

    async def get_task(self, task_id: str) -> Dict:
        return await self._request("GET", f"/tasks/{task_id}")

    async def update_task(
        self,
        task_id: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        body: Dict = {}
        if description is not None:
            body["description"] = description
        if priority is not None:
            body["priority"] = priority
        if status is not None:
            body["status"] = status
        if metadata is not None:
            body["metadata"] = metadata
        return await self._request("PUT", f"/tasks/{task_id}", json=body)

    async def delete_task(self, task_id: str) -> Dict:
        return await self._request("DELETE", f"/tasks/{task_id}")

    async def list_agents(self) -> List[Dict]:
        return await self._request("GET", "/agents")

    async def get_agent(self, agent_name: str) -> Dict:
        return await self._request("GET", f"/agents/{agent_name}")

    async def execute_task_on_agent(self, agent_name: str, task: str) -> Dict:
        return await self._request("POST", f"/agents/{agent_name}/execute", json={"task": task})

    async def get_status(self) -> Dict:
        return await self._request("GET", "/status")

    async def get_metrics(self) -> Dict:
        return await self._request("GET", "/metrics")

    async def health_check(self) -> Dict:
        return await self._request("GET", "/health")

    async def get_memories(self, agent: str, memory_type: Optional[str] = None) -> List[Dict]:
        params = {}
        if memory_type:
            params["memory_type"] = memory_type
        return await self._request("GET", f"/memory/{agent}", params=params)

    async def add_memory(
        self,
        agent: str,
        content: Dict,
        memory_type: str = "episodic",
        keywords: Optional[List[str]] = None,
        importance: float = 0.5,
    ) -> Dict:
        body = {"content": content, "memory_type": memory_type, "importance": importance}
        if keywords:
            body["keywords"] = keywords
        return await self._request("POST", f"/memory/{agent}", json=body)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cli():
    import argparse

    parser = argparse.ArgumentParser(description="AI OS API Client")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    sub = parser.add_subparsers(dest="command", required=True)

    # tasks
    p = sub.add_parser("tasks", help="List tasks")
    p.add_argument("--status")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--offset", type=int, default=0)

    p = sub.add_parser("create-task", help="Create a task")
    p.add_argument("description")
    p.add_argument("--priority", default="medium")
    p.add_argument("--metadata", type=json.loads, default=None)

    p = sub.add_parser("get-task", help="Get task by ID")
    p.add_argument("task_id")

    p = sub.add_parser("delete-task", help="Delete a task")
    p.add_argument("task_id")

    # agents
    sub.add_parser("agents", help="List agents")

    p = sub.add_parser("agent", help="Get agent details")
    p.add_argument("agent_name")

    p = sub.add_parser("execute", help="Execute a task on an agent")
    p.add_argument("agent_name")
    p.add_argument("task")

    # system
    sub.add_parser("status", help="Get system status")
    sub.add_parser("metrics", help="Get system metrics")
    sub.add_parser("health", help="Health check")

    # memory
    p = sub.add_parser("memories", help="Get agent memories")
    p.add_argument("agent_name")
    p.add_argument("--type")

    p = sub.add_parser("add-memory", help="Add a memory")
    p.add_argument("agent_name")
    p.add_argument("content", type=json.loads)
    p.add_argument("--type", dest="memory_type", default="episodic")
    p.add_argument("--importance", type=float, default=0.5)
    p.add_argument("--keywords", nargs="*", default=[])

    args = parser.parse_args()

    client = AIOSClient(args.url)

    try:
        if args.command == "tasks":
            result = client.list_tasks(status=args.status, limit=args.limit, offset=args.offset)
        elif args.command == "create-task":
            result = client.create_task(args.description, priority=args.priority, metadata=args.metadata)
        elif args.command == "get-task":
            result = client.get_task(args.task_id)
        elif args.command == "delete-task":
            result = client.delete_task(args.task_id)
        elif args.command == "agents":
            result = client.list_agents()
        elif args.command == "agent":
            result = client.get_agent(args.agent_name)
        elif args.command == "execute":
            result = client.execute_task_on_agent(args.agent_name, args.task)
        elif args.command == "status":
            result = client.get_status()
        elif args.command == "metrics":
            result = client.get_metrics()
        elif args.command == "health":
            result = client.health_check()
        elif args.command == "memories":
            result = client.get_memories(args.agent_name, memory_type=args.type)
        elif args.command == "add-memory":
            result = client.add_memory(args.agent_name, args.content,
                                       memory_type=args.memory_type,
                                       importance=args.importance,
                                       keywords=args.keywords)
        else:
            parser.print_help()
            return

        print(json.dumps(result, indent=2, default=str))
    finally:
        client.close()


if __name__ == "__main__":
    _cli()
