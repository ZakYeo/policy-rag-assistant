import Markdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';

// Underline uses <u> because CommonMark has no underline syntax. Parse HTML,
// then retain only these presentation elements, with no attributes or URLs.
const schema = {
  tagNames: ['p', 'br', 'strong', 'em', 'u', 'code', 'pre', 'ul', 'ol', 'li', 'blockquote'],
  attributes: {},
  strip: ['script', 'style', 'iframe', 'object', 'svg', 'math'],
};

export function AnswerText({ text, extractive = false }: { text: string; extractive?: boolean }) {
  return <div className="answer-text reveal text-[1.3rem] leading-[1.7] [overflow-wrap:anywhere]">
    {extractive ? <p className="whitespace-pre-wrap">{text}</p>
      : <Markdown rehypePlugins={[rehypeRaw, [rehypeSanitize, schema]]}>{text}</Markdown>}
  </div>;
}
