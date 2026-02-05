from dataclasses import dataclass
from pathlib import Path
import os

@dataclass
class PromptTemplates:
    system: str
    user: str

class PromptBuilder:
    """
    Loads prompt templates from configs/prompts and injects retrieved context.
    """
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir
        self.templates = self._load_templates()

    def _load_templates(self) -> PromptTemplates:
        system_path = self.prompts_dir / "rag_system.txt"
        user_path = self.prompts_dir / "rag_user_template.txt"
        system = system_path.read_text(encoding="utf-8")
        user = user_path.read_text(encoding="utf-8")
        return PromptTemplates(system=system.strip(), user=user.strip())

    def build_context(self, retrieved, max_chars: int = 4500) -> str:
        out, total = [], 0
        for r in retrieved:
            header = (
                f'[SOURCE: {os.path.basename(r["source"])} | {r["chunk_id"]} | '
                f'strategy={r.get("strategy")} | bm25_rank={r.get("bm25_rank")} | dense_rank={r.get("dense_rank")}]\n'
            )
            block = header + r["text"] + "\n"
            if total + len(block) > max_chars:
                break
            out.append(block)
            total += len(block)
        return "\n".join(out).strip()

    def build_prompt(self, query: str, retrieved) -> str:
        context = self.build_context(retrieved)

        # User template may include placeholders
        user_msg = self.templates.user.format(question=query, context=context)

        # Final prompt is system + user (Gemma friendly: put rules inside text)
        return f"{self.templates.system}\n\n{user_msg}".strip()
