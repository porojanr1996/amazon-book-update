import axios from 'axios';
import pino from 'pino';

const logger = pino({ name: 'ai-diagnostics' });

interface DiagnosticRequest {
  errorMessage: string;
  stackTrace?: string;
  htmlSnippet?: string;
  selector?: string;
}

interface DiagnosticResult {
  suggestedSelector: string;
  reasoning: string;
}

export class OllamaDiagnostics {
  private ollamaUrl: string;
  private model: string;

  constructor(ollamaUrl: string = 'http://localhost:11434', model: string = 'codellama') {
    this.ollamaUrl = ollamaUrl;
    this.model = model;
  }

  async diagnoseScrapingError(request: DiagnosticRequest): Promise<DiagnosticResult> {
    logger.info('Running AI diagnostics on scraping error...');

    const prompt = this.buildPrompt(request);

    try {
      const response = await axios.post(`${this.ollamaUrl}/api/generate`, {
        model: this.model,
        prompt,
        stream: false,
      });

      const aiResponse = response.data.response;
      logger.info('AI diagnostics completed');

      // Parse AI response for selector suggestion
      const selectorMatch = aiResponse.match(/selector[:\s]+(.*?)(?:\n|$)/i);
      const suggestedSelector = selectorMatch ? selectorMatch[1].trim() : '';

      return {
        suggestedSelector,
        reasoning: aiResponse,
      };

    } catch (error) {
      logger.error('Ollama diagnostics failed:', error);
      throw new Error(`Failed to run diagnostics: ${error}`);
    }
  }

  private buildPrompt(request: DiagnosticRequest): string {
    let prompt = `You are a web scraping expert. A Playwright scraper failed to extract the "Best Sellers Rank" from an Amazon product page.\n\n`;
    
    prompt += `Error: ${request.errorMessage}\n\n`;
    
    if (request.stackTrace) {
      prompt += `Stack Trace:\n${request.stackTrace.substring(0, 500)}\n\n`;
    }
    
    if (request.selector) {
      prompt += `Selector used: ${request.selector}\n\n`;
    }
    
    if (request.htmlSnippet) {
      prompt += `HTML Snippet:\n${request.htmlSnippet.substring(0, 1000)}\n\n`;
    }
    
    prompt += `Task: Suggest a new Playwright selector to extract the Amazon Best Sellers Rank.\n\n`;
    prompt += `Requirements:\n`;
    prompt += `- The selector should target text containing "Best Sellers Rank"\n`;
    prompt += `- It should extract the rank number (e.g., #12,345)\n`;
    prompt += `- Provide only the selector string\n`;
    prompt += `- Format: selector: <your-selector-here>\n\n`;
    prompt += `Your response:`;

    return prompt;
  }
}

export async function runDiagnostics(request: DiagnosticRequest): Promise<DiagnosticResult> {
  const diagnostics = new OllamaDiagnostics();
  return diagnostics.diagnoseScrapingError(request);
}
