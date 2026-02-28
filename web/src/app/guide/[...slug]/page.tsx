import { getDocBySlug, getAllDocs } from '@/lib/docs';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { notFound } from 'next/navigation';
import 'highlight.js/styles/github-dark.css';

export async function generateStaticParams() {
  const docs = getAllDocs();
  return docs.map((doc) => ({
    slug: doc.slug,
  }));
}

export default async function DocPage({ params }: { params: Promise<{ slug: string[] }> }) {
  const resolvedParams = await params;
  const doc = getDocBySlug(resolvedParams.slug);

  if (!doc) {
    notFound();
  }

  return (
    <article className="animate-fade-in max-w-4xl mx-auto">
      <div className="mb-8 border-b border-white/10 pb-6">
        <h1 className="mb-4 text-4xl font-bold tracking-tight text-white">{doc.title}</h1>
        <div className="flex items-center gap-3 text-sm text-gray-400">
          <span className="bg-blue-500/10 text-blue-400 px-2.5 py-1 rounded-full text-xs font-medium uppercase tracking-wide border border-blue-500/20">
            {doc.category}
          </span>
          <span className="w-1 h-1 bg-gray-600 rounded-full"></span>
          <span>Reading time: {Math.ceil(doc.content.split(/\s+/).length / 200)} min</span>
        </div>
      </div>
      
      <div className="prose prose-invert prose-blue max-w-none">
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]} 
          rehypePlugins={[rehypeHighlight]}
          components={{
            pre: ({node, ...props}) => (
              <pre className="bg-zinc-900 border border-white/10 rounded-lg p-4 overflow-x-auto my-6 shadow-xl" {...props} />
            ),
            code: ({node, className, children, ...props}) => {
              const match = /language-(\w+)/.exec(className || '')
              return !match ? (
                <code className="bg-white/10 rounded px-1.5 py-0.5 text-sm font-mono text-blue-200 border border-white/5" {...props}>
                  {children}
                </code>
              ) : (
                <code className={className} {...props}>
                  {children}
                </code>
              )
            },
            table: ({node, ...props}) => (
              <div className="overflow-x-auto my-8 border border-white/10 rounded-lg shadow-sm">
                <table className="w-full text-left text-sm border-collapse" {...props} />
              </div>
            ),
            thead: ({node, ...props}) => (
              <thead className="bg-zinc-900/50 border-b border-white/10" {...props} />
            ),
            th: ({node, ...props}) => (
              <th className="px-6 py-4 font-semibold text-white whitespace-nowrap" {...props} />
            ),
            td: ({node, ...props}) => (
              <td className="px-6 py-4 border-b border-white/5 text-gray-300 last:border-0" {...props} />
            ),
            blockquote: ({node, ...props}) => (
              <blockquote className="border-l-4 border-blue-500 pl-6 py-2 italic text-gray-300 my-8 bg-blue-500/5 rounded-r-lg" {...props} />
            ),
            a: ({node, ...props}) => (
              <a className="text-blue-400 hover:text-blue-300 underline underline-offset-4 decoration-blue-400/30 hover:decoration-blue-400 transition-colors" {...props} />
            ),
            h1: ({node, ...props}) => <h1 className="text-3xl font-bold mt-16 mb-8 text-white scroll-mt-20" {...props} />,
            h2: ({node, ...props}) => <h2 className="text-2xl font-bold mt-12 mb-6 text-white border-b border-white/10 pb-2 scroll-mt-20 flex items-center gap-2" {...props} />,
            h3: ({node, ...props}) => <h3 className="text-xl font-bold mt-8 mb-4 text-white scroll-mt-20" {...props} />,
            ul: ({node, ...props}) => <ul className="list-disc list-outside ml-6 space-y-2 my-6 text-gray-300 marker:text-blue-500" {...props} />,
            ol: ({node, ...props}) => <ol className="list-decimal list-outside ml-6 space-y-2 my-6 text-gray-300 marker:text-blue-500" {...props} />,
            p: ({node, ...props}) => <p className="leading-7 my-6 text-gray-300" {...props} />,
            hr: ({node, ...props}) => <hr className="my-12 border-white/10" {...props} />,
            img: ({node, ...props}) => <img className="rounded-lg border border-white/10 shadow-lg my-8 w-full object-cover" {...props} />,
          }}
        >
          {doc.content}
        </ReactMarkdown>
      </div>
    </article>
  );
}
