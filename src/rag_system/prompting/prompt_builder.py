from dataclasses import dataclass
from pathlib import Path
import os
import xml.etree.ElementTree as ET

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
        user_path = self.prompts_dir / "rag_user_template.xml"  # Changed from .txt
        system = system_path.read_text(encoding="utf-8")
        
        # Parse XML user template
        tree = ET.parse(user_path)
        root = tree.getroot()
        context_template = root.find("context").text or "{context}"
        question_template = root.find("question").text or "{question}"
        instructions = root.find("instructions").text or ""
        
        user = f"CONTEXT:\n{context_template}\n\nQUESTION:\n{question_template}\n\n{instructions}"
        return PromptTemplates(system=system.strip(), user=user.strip())

    def build_context(self, retrieved, max_chars: int = 4500) -> str:
        out, total = [], 0
        for r in retrieved:
            source = r.get("source", "")
            chunk_id = r.get("chunk_id", "")
            
            # Extract just the filename
            filename = source.split("/")[-1] if source else "unknown"
            
            # Extract just the chunk number from chunk_id (e.g., "lstm.pdf::fixed::chunk24" -> "24")
            chunk_num = "?"
            if "::" in chunk_id:
                parts = chunk_id.split("::")
                last_part = parts[-1]
                if last_part.startswith("chunk"):
                    chunk_num = last_part.replace("chunk", "")
            
            header = (
                f'[SOURCE: {filename} (chunk {chunk_num})]'
            )
            block = header + "\n" + r["text"] + "\n"
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
