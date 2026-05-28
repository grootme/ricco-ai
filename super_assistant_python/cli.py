#!/usr/bin/env python3
"""
Super Asistente Cognitivo - CLI
================================

Interfaz de línea de comandos para el ecosistema.
"""

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from super_assistant.agents.base import AgentFactory
from super_assistant.memory.system import CognitiveMemorySystem, SQLiteMemoryStore
from super_assistant.skills.registry import SkillRegistry, initialize_builtin_skills

app = typer.Typer(
    name="super-assistant",
    help="🧠 Super Asistente Cognitivo con Capital Cognitivo"
)
console = Console()


# ============================================
# ECOSYSTEM COMMANDS
# ============================================

@app.command()
def init():
    """🚀 Inicializar el ecosistema"""
    console.print(Panel.fit(
        "🧠 [bold]Super Asistente Cognitivo[/bold]\n"
        "Inicializando ecosistema...",
        border_style="blue"
    ))
    
    async def _init():
        # Crear Lead Agent
        console.print("[cyan]Creating Lead Agent...[/cyan]")
        lead = AgentFactory.create_lead_agent()
        
        # Crear subagentes
        console.print("[cyan]Creating subagents...[/cyan]")
        subagents = {
            "Researcher": AgentFactory.create_researcher(),
            "Analyzer": AgentFactory.create_analyzer(),
            "Builder": AgentFactory.create_builder(),
            "Validator": AgentFactory.create_validator(),
            "Memory": AgentFactory.create_memory_agent(),
            "Security": AgentFactory.create_security_agent(),
        }
        
        # Registrar subagentes
        for name, subagent in subagents.items():
            lead.register_subagent(subagent)
            console.print(f"  ✓ [green]{name} Agent[/green] registered")
        
        # Inicializar skills
        console.print("[cyan]Loading skills...[/cyan]")
        registry = SkillRegistry()
        skills = await initialize_builtin_skills(registry)
        console.print(f"  ✓ [green]{len(skills)}[/green] builtin skills loaded")
        
        # Iniciar agentes
        console.print("[cyan]Starting agents...[/cyan]")
        await lead.start()
        
        console.print()
        console.print(Panel.fit(
            "✅ [bold green]Ecosystem initialized successfully![/bold green]\n\n"
            f"• Lead Agent: [bold]{lead.name}[/bold]\n"
            f"• Subagents: [bold]{len(subagents)}[/bold]\n"
            f"• Skills: [bold]{len(skills)}[/bold]\n\n"
            "Run [bold]super-assistant api[/bold] to start the API server",
            border_style="green"
        ))
    
    asyncio.run(_init())


@app.command()
def status():
    """📊 Mostrar estado del ecosistema"""
    console.print("[cyan]Checking ecosystem status...[/cyan]")
    
    # Verificar inicialización
    table = Table(title="Ecosystem Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")
    
    # Verificar directorios
    data_dir = Path("data")
    skills_dir = Path("skills/local")
    
    table.add_row("Data Directory", "✓" if data_dir.exists() else "✗", str(data_dir))
    table.add_row("Skills Directory", "✓" if skills_dir.exists() else "✗", str(skills_dir))
    
    # Verificar base de datos
    db_file = data_dir / "super_assistant.db"
    table.add_row("Database", "✓" if db_file.exists() else "✗", str(db_file))
    
    console.print(table)


@app.command()
def agents():
    """🤖 Listar agentes disponibles"""
    console.print("[cyan]Available Agent Types:[/cyan]")
    
    table = Table()
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    table.add_column("HITL")
    
    agent_types = [
        ("LEAD", "Lead Agent", "Orquestador principal del ecosistema", "✓"),
        ("RESEARCHER", "Researcher Agent", "Investigación profunda y síntesis", "✗"),
        ("ANALYZER", "Analyzer Agent", "Análisis de datos y detección de patrones", "✗"),
        ("BUILDER", "Builder Agent", "Constructor de nuevos agentes", "✓"),
        ("VALIDATOR", "Validator Agent", "Validación y testing", "✗"),
        ("MEMORY", "Memory Agent", "Gestión de memoria y conocimiento", "✗"),
        ("SECURITY", "Security Agent", "Evaluación de seguridad", "✓"),
    ]
    
    for type_, name, desc, hitl in agent_types:
        table.add_row(type_, name, desc, hitl)
    
    console.print(table)


@app.command()
def skills():
    """🔧 Listar skills disponibles"""
    async def _list_skills():
        registry = SkillRegistry()
        await registry.load_all_from_disk()
        skills_list = await registry.list_local()
        
        if not skills_list:
            console.print("[yellow]No skills found. Run 'init' first.[/yellow]")
            return
        
        table = Table(title=f"Local Skills ({len(skills_list)})")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="green")
        table.add_column("Status")
        table.add_column("Tags")
        
        for skill in skills_list:
            table.add_row(
                skill.name,
                skill.category.value,
                skill.status.value,
                ", ".join(skill.tags[:3])
            )
        
        console.print(table)
    
    asyncio.run(_list_skills())


# ============================================
# API COMMANDS
# ============================================

@app.command()
def api(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload")
):
    """🌐 Iniciar servidor API"""
    console.print(f"[cyan]Starting API server on {host}:{port}...[/cyan]")
    
    import uvicorn
    uvicorn.run(
        "super_assistant.api.main:app",
        host=host,
        port=port,
        reload=reload
    )


# ============================================
# MEMORY COMMANDS
# ============================================

@app.command()
def memory_stats():
    """📊 Mostrar estadísticas de memoria"""
    async def _stats():
        memory_system = CognitiveMemorySystem(
            sqlite_store=SQLiteMemoryStore()
        )
        
        # Contar memorias
        all_memories = await memory_system.session_store.search("", limit=1000)
        
        table = Table(title="Memory Statistics")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")
        
        type_counts = {}
        for m in all_memories:
            type_counts[m.type.value] = type_counts.get(m.type.value, 0) + 1
        
        for type_, count in type_counts.items():
            table.add_row(type_, str(count))
        
        table.add_row("[bold]Total[/bold]", f"[bold]{len(all_memories)}[/bold]")
        
        console.print(table)
    
    asyncio.run(_stats())


# ============================================
# CHAT COMMAND
# ============================================

@app.command()
def chat():
    """💬 Iniciar sesión de chat con el Lead Agent"""
    console.print(Panel.fit(
        "💬 [bold]Chat with Lead Agent[/bold]\n"
        "Type 'exit' to quit\n",
        border_style="blue"
    ))
    
    async def _chat():
        # Crear ecosistema
        lead = AgentFactory.create_default_ecosystem()
        await lead.start()
        
        console.print("[green]Lead Agent is ready. Start chatting![/green]\n")
        
        while True:
            try:
                user_input = console.input("[bold cyan]You:[/bold cyan] ")
                
                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if not user_input.strip():
                    continue
                
                # Ejecutar agente
                console.print("[dim]Thinking...[/dim]")
                result = await lead.execute({"query": user_input})
                
                # Mostrar respuesta
                console.print(f"\n[bold purple]Assistant:[/bold purple] {result}\n")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
    
    asyncio.run(_chat())


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    app()
