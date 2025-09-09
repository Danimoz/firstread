import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

interface ContractHtmlOptions {
  contractId?: string
  content: string
}

export function generateContractHtml({ contractId, content }: ContractHtmlOptions): string {
  const contractTitle = "Service Agreement"
  const formattedContent = content
    .replace(/\n/g, '<br/>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

  const htmlTemplate = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${contractTitle}</title>
    <style>
        body {
            font-family: "Times New Roman", Times, serif;
            max-width: 8.5in;
            margin: 0 auto;
            padding: 1in;
            background: white;
            color: black;
            line-height: 1.6;
        }
        
        h1 {
            text-align: center;
            font-size: 18pt;
            font-weight: bold;
            margin-bottom: 24pt;
            text-transform: uppercase;
            color: black;
        }
        
        h2 {
            font-size: 14pt;
            font-weight: bold;
            margin-top: 18pt;
            margin-bottom: 12pt;
            color: black;
        }
        
        h3 {
            font-size: 12pt;
            font-weight: bold;
            margin-top: 12pt;
            margin-bottom: 6pt;
            color: black;
        }
        
        p {
            font-size: 12pt;
            margin-bottom: 12pt;
            text-align: justify;
            color: black;
        }
        
        /* Specific styling for sub-sections and clauses */
        .contract-content {
            white-space: pre-wrap;
        }
        
        /* Ensure numbered sub-sections start on new lines */
        .contract-content br + span:first-child,
        .contract-content p span:first-child {
            display: inline-block;
            margin-top: 8pt;
        }
        
        /* Style for numbered clauses */
        .clause-number {
            font-weight: bold;
            display: inline-block;
            margin-top: 8pt;
        }
        
        /* Better line height for dense legal text */
        .legal-text {
            line-height: 1.4;
        }
        
        /* Paragraph spacing */
        .section {
            margin-bottom: 16pt;
        }
        
        /* Force line breaks to be visible */
        br {
            display: block;
            margin: 4pt 0;
            content: "";
        }
        
        @media print {
            body {
                padding: 0.5in;
            }
            
            @page {
                margin: 0.5in;
                size: letter;
            }
        }
    </style>
</head>
<body>
    <h1>${contractTitle}</h1>
    <div class="contract-content legal-text">
        ${formattedContent}
    </div>
</body>
</html>`

  return htmlTemplate
}