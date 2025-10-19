import { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
}

export default function MermaidDiagram({ chart }: MermaidDiagramProps) {
  const elementRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fix hydration mismatch by only rendering after mount
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    const currentElement = elementRef.current;

    if (!currentElement) return;

    const renderDiagram = async () => {
      setError(null);
      try {
        const { svg } = await mermaid.render(`mermaid-svg-${Date.now()}`, chart);
        currentElement.innerHTML = svg;
      } catch (e: unknown) {
        if (e instanceof Error) {
          setError(e.message || 'Failed to render diagram');
        }
        currentElement.innerHTML = '';
      }
    };

    renderDiagram();
  }, [chart]);

  // Don't render anything until mounted (prevents hydration mismatch)
  if (!mounted) {
    return (
      <div className="bg-white p-4 rounded-lg border border-gray-200 dark:bg-gray-800 dark:border-gray-600 my-4 text-center overflow-x-auto">
        <div className="animate-pulse h-32 bg-gray-200 dark:bg-gray-700 rounded"></div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 my-4 dark:bg-red-900/20 dark:border-red-800">
        <div className="text-red-700 dark:text-red-300 text-sm">
          <strong>Diagram Error:</strong> {error}
        </div>
        <details className="mt-2">
          <summary className="cursor-pointer text-xs">Show chart content</summary>
          <pre className="text-xs mt-2 p-2 bg-gray-100 dark:bg-gray-700 rounded overflow-x-auto">
            {chart}
          </pre>
        </details>
      </div>
    );
  }

  return (
    <div 
      ref={elementRef}
      className="mermaid bg-white p-4 rounded-lg border border-gray-200 dark:bg-gray-800 dark:border-gray-600 my-4 text-center overflow-x-auto min-h-[100px]"
    />
  );
}