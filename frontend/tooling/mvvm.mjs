import path from 'node:path';

const layers = ['contracts', 'models', 'viewmodels', 'views', 'composition'];
const allowed = {
  contracts: ['contracts'],
  models: ['contracts', 'models'],
  viewmodels: ['contracts', 'models', 'viewmodels'],
  views: ['contracts', 'views'],
  composition: layers,
};
const applicationHooks = new Set([
  'useState', 'useReducer', 'useEffect', 'useLayoutEffect', 'useSyncExternalStore',
  'useTransition', 'useDeferredValue', 'useActionState', 'useOptimistic',
]);
const browserIO = new Set(['fetch', 'localStorage', 'sessionStorage', 'document', 'window', 'navigator', 'WebSocket', 'EventSource']);
const layerOf = (filename) => filename.replaceAll('\\', '/').match(/\/src\/(contracts|models|viewmodels|views|composition)(?:\/|$)/)?.[1];

export default {
  meta: {
    type: 'problem',
    docs: { description: 'Enforce the NorthStar frontend MVVM dependency and side-effect boundaries.' },
    schema: [],
    messages: { boundary: '{{reason}}' },
  },
  create(context) {
    const filename = context.filename;
    const layer = layerOf(filename);
    if (!layer) return {};
    const reactNamespaces = new Set();
    const report = (node, reason) => context.report({ node, messageId: 'boundary', data: { reason } });
    const imports = (node) => {
      const source = node.source?.value;
      if (typeof source !== 'string') return;
      if (source.startsWith('react') && ['models', 'contracts'].includes(layer)) {
        report(node, `${layer} must not depend on React.`);
      }
      if (source === 'react' && layer === 'views') {
        for (const specifier of node.specifiers ?? []) {
          if (specifier.type === 'ImportDefaultSpecifier' || specifier.type === 'ImportNamespaceSpecifier') {
            reactNamespaces.add(specifier.local.name);
          }
          if (applicationHooks.has(specifier.imported?.name)) {
            report(specifier, 'Application state and effects belong in ViewModels.');
          }
        }
      }
      if (source.startsWith('.') || source.startsWith('@/')) {
        const resolved = source.startsWith('@/')
          ? filename.slice(0, filename.indexOf('/src/')) + '/src/' + source.slice(2)
          : path.resolve(path.dirname(filename), source);
        const target = layerOf(resolved);
        if (!target || !allowed[layer].includes(target)) {
          report(node, `${layer} may not import or re-export ${target ?? 'unclassified local modules'}.`);
        }
      }
    };
    return {
      ImportDeclaration: imports,
      ExportNamedDeclaration: imports,
      ExportAllDeclaration: imports,
      ImportExpression(node) { imports({ ...node, source: node.source }); },
      JSXElement(node) {
        if (['models', 'viewmodels', 'contracts'].includes(layer)) report(node, 'JSX belongs in Views or the composition root.');
      },
      JSXFragment(node) {
        if (['models', 'viewmodels', 'contracts'].includes(layer)) report(node, 'JSX belongs in Views or the composition root.');
      },
      MemberExpression(node) {
        if (!['views', 'viewmodels', 'contracts'].includes(layer)) return;
        if (node.object.type === 'Identifier' && browserIO.has(node.object.name)) {
          report(node, 'Browser I/O belongs in Models.');
        } else if (node.object.type === 'Identifier' && ['globalThis', 'self'].includes(node.object.name)
            && browserIO.has(node.property.name ?? node.property.value)) {
          report(node, 'Browser I/O belongs in Models.');
        } else if (layer === 'views' && reactNamespaces.has(node.object.name)
            && applicationHooks.has(node.property.name ?? node.property.value)) {
          report(node, 'Application state and effects belong in ViewModels.');
        }
      },
      CallExpression(node) {
        if (node.callee.name === 'require' && node.arguments[0]) imports({ ...node, source: node.arguments[0] });
        if (['views', 'viewmodels', 'contracts'].includes(layer) && browserIO.has(node.callee.name)) {
          report(node, 'Browser I/O belongs in Models.');
        }
      },
      VariableDeclarator(node) {
        if (['views', 'viewmodels', 'contracts'].includes(layer) && node.init?.type === 'Identifier'
            && (browserIO.has(node.init.name) || ['globalThis', 'self'].includes(node.init.name))) {
          report(node, 'Browser I/O aliases belong in Models.');
        }
      },
    };
  },
};
