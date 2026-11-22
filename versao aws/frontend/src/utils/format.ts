// Formatação compartilhada pela interface.

/** Nota de 0 a 1 com 4 casas, como nas tabelas da monografia (ex.: 0,9932). */
export function score(n: number | null | undefined): string {
  if (n === null || n === undefined) return "—";
  return n.toLocaleString("pt-BR", { minimumFractionDigits: 4, maximumFractionDigits: 4 });
}

export function seconds(n: number): string {
  return `${n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} s`;
}

const STATUS: Record<string, string> = {
  uploading: "enviando",
  pending: "na fila",
  processing: "processando",
  done: "pronto",
  error: "erro",
};

export function statusLabel(s: string): string {
  return STATUS[s] ?? s;
}

const TOOLS: Record<string, string> = {
  buscar_no_material: "Buscou no material",
  listar_topicos: "Listou os assuntos",
  resumir_material: "Leu o material para resumir",
  pedir_esclarecimento: "Pediu esclarecimento",
};

export function toolLabel(t: string): string {
  return TOOLS[t] ?? t;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Markdown mínimo das respostas do modelo: negrito, itálico, código e listas.
 * O texto é escapado antes, então nada que o modelo escreva vira HTML de verdade.
 */
export function miniMarkdown(text: string): string {
  const inline = (s: string) =>
    escapeHtml(s)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");

  const out: string[] = [];
  let list: "ul" | "ol" | null = null;
  const closeList = () => {
    if (list) out.push(`</${list}>`);
    list = null;
  };

  for (const raw of text.split("\n")) {
    const line = raw.trimEnd();
    const ul = line.match(/^\s*[-*•]\s+(.*)$/);
    const ol = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (ul || ol) {
      const kind = ul ? "ul" : "ol";
      if (list !== kind) {
        closeList();
        out.push(`<${kind}>`);
        list = kind;
      }
      out.push(`<li>${inline((ul ?? ol)![1])}</li>`);
      continue;
    }
    closeList();
    const heading = line.match(/^#{1,4}\s+(.*)$/);
    if (heading) out.push(`<p><strong>${inline(heading[1])}</strong></p>`);
    else if (line.trim() === "---") out.push("<hr />");
    else if (line.trim()) out.push(`<p>${inline(line)}</p>`);
  }
  closeList();
  return out.join("");
}
