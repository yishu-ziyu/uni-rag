"""uni-rag CLI."""
from __future__ import annotations
from pathlib import Path
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from uni_rag.rag.pipeline import RAGPipeline
from uni_rag.api.app import create_app
import uvicorn

app = typer.Typer(help="uni-rag: 通用 RAG 助手")
console = Console()


@app.command()
def ingest(file: Path = typer.Argument(..., exists=True)):
    """上传并入库一个文档。"""
    pipeline = RAGPipeline()
    result = pipeline.ingest_file(file)
    console.print(Panel(
        f"[bold]{file.name}[/bold]\n"
        f"格式: {result['format']}\n"
        f"chunks: {result['chunks']}\n"
        f"ID: {result['source_id']}",
        title="✓ 已入库",
    ))


@app.command()
def ask(
    question: str = typer.Argument(...),
    session: str | None = typer.Option(None, "--session", "-s", help="会话 ID（追问用）"),
):
    """问一个问题。"""
    pipeline = RAGPipeline()
    result = pipeline.query(question, session_id=session)
    console.print(Panel(Markdown(result["answer"]), title="答"))
    if result["citations"]:
        console.print("\n[bold]引用：[/bold]")
        for c in result["citations"]:
            console.print(f"  • [cyan]{c['source']}[/cyan]" + (f" · {c['section']}" if c.get("section") else ""))
        if not session:
            console.print(f"\n[dim]提示: 用 -s <id> 追问。当前 session: {result.get('session_id', 'N/A')}[/dim]")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8765, "--port", "-p"),
):
    """起 Web 服务。"""
    uvicorn.run("uni_rag.api.app:create_app", factory=True, host=host, port=port)


if __name__ == "__main__":
    app()
