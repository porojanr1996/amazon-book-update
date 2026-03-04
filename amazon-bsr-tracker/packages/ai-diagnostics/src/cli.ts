#!/usr/bin/env ts-node

import { runDiagnostics } from './index';
import { readFileSync } from 'fs';

const errorFile = process.argv[2];
const htmlFile = process.argv[3];

if (!errorFile) {
  console.error('Usage: npm run diagnose <error-file> [html-file]');
  console.error('Example: npm run diagnose ./errors/error.txt ./errors/html.html');
  process.exit(1);
}

(async () => {
  try {
    const errorMessage = readFileSync(errorFile, 'utf-8');
    const htmlSnippet = htmlFile ? readFileSync(htmlFile, 'utf-8') : undefined;

    console.log('🤖 Running AI diagnostics...');
    
    const result = await runDiagnostics({
      errorMessage,
      htmlSnippet,
    });

    console.log('\n✅ Diagnostic Results:');
    console.log(`\nSuggested Selector: ${result.suggestedSelector}`);
    console.log(`\nReasoning:\n${result.reasoning}`);

  } catch (error) {
    console.error('❌ Diagnostics failed:', error);
    process.exit(1);
  }
})();
