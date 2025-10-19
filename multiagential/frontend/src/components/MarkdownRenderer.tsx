'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface MarkdownRendererProps {
  children: string;
}

export default function MarkdownRenderer({ children }: MarkdownRendererProps) {
  return (
    <div className="markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ node, ...props }) => <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4 mt-6" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-3 mt-5" {...props} />,
          h3: ({ node, ...props }) => <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2 mt-4" {...props} />,
          h4: ({ node, ...props }) => <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-2 mt-3" {...props} />,
          p: ({ node, ...props }) => <p className="text-gray-800 dark:text-gray-200 mb-4 leading-relaxed" {...props} />,
          ul: ({ node, ...props }) => <ul className="list-disc list-inside text-gray-800 dark:text-gray-200 mb-4 space-y-2" {...props} />,
          ol: ({ node, ...props }) => <ol className="list-decimal list-inside text-gray-800 dark:text-gray-200 mb-4 space-y-2" {...props} />,
          li: ({ node, ...props }) => <li className="text-gray-800 dark:text-gray-200 ml-4" {...props} />,
          blockquote: ({ node, ...props }) => <blockquote className="border-l-4 border-blue-500 pl-4 italic text-gray-700 dark:text-gray-300 my-4" {...props} />,
          strong: ({ node, ...props }) => <strong className="font-bold text-gray-900 dark:text-white" {...props} />,
          em: ({ node, ...props }) => <em className="italic text-gray-800 dark:text-gray-200" {...props} />,
          a: ({ node, ...props }) => <a className="text-blue-600 dark:text-blue-400 hover:underline" {...props} />,
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || '');
            return !inline && match ? (
              <SyntaxHighlighter
                style={vscDarkPlus as any}
                language={match[1]}
                PreTag="div"
                className="rounded-lg my-4"
                {...props}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            ) : (
              <code className="bg-gray-100 dark:bg-gray-800 text-red-600 dark:text-red-400 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                {children}
              </code>
            );
          },
          hr: ({ node, ...props }) => <hr className="my-6 border-gray-300 dark:border-gray-700" {...props} />,
          table: ({ node, ...props }) => <div className="overflow-x-auto my-4"><table className="min-w-full border border-gray-300 dark:border-gray-700" {...props} /></div>,
          th: ({ node, ...props }) => <th className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white font-semibold px-4 py-2 border border-gray-300 dark:border-gray-700" {...props} />,
          td: ({ node, ...props }) => <td className="text-gray-800 dark:text-gray-200 px-4 py-2 border border-gray-300 dark:border-gray-700" {...props} />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
