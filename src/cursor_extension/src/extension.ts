import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export function activate(context: vscode.ExtensionContext) {
    console.log('Cursor Claude Integration is now active');

    let disposable = vscode.commands.registerCommand('cursor-claude.generateCode', async () => {
        try {
            // Get the specification file
            const specFiles = await vscode.workspace.findFiles('specs/*.json');
            if (specFiles.length === 0) {
                vscode.window.showErrorMessage('No specification files found in specs/ directory');
                return;
            }

            // If multiple specs found, let user choose
            let specFile: vscode.Uri;
            if (specFiles.length === 1) {
                specFile = specFiles[0];
            } else {
                const items = specFiles.map(file => ({
                    label: path.basename(file.fsPath),
                    description: file.fsPath,
                    file
                }));
                
                const selected = await vscode.window.showQuickPick(items, {
                    placeHolder: 'Select a specification file'
                });
                
                if (!selected) {
                    return;
                }
                specFile = selected.file;
            }

            // Read and parse the specification
            const specContent = await fs.promises.readFile(specFile.fsPath, 'utf8');
            const spec = JSON.parse(specContent);

            // Create output directory
            const projectName = spec.title.toLowerCase().replace(/\s+/g, '_');
            const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
            if (!workspaceFolder) {
                vscode.window.showErrorMessage('No workspace folder found');
                return;
            }

            const outputDir = path.join(workspaceFolder.uri.fsPath, 'generated_projects', projectName);
            await fs.promises.mkdir(outputDir, { recursive: true });

            // Generate instructions markdown
            const instructions = generateInstructions(spec);
            const instructionsPath = path.join(outputDir, 'INSTRUCTIONS.md');
            await fs.promises.writeFile(instructionsPath, instructions);

            // Open the instructions file
            const doc = await vscode.workspace.openTextDocument(instructionsPath);
            await vscode.window.showTextDocument(doc);

            // Trigger Cursor's code generation
            await vscode.commands.executeCommand('cursor.generateCode');

            vscode.window.showInformationMessage('Code generation started');
        } catch (error) {
            vscode.window.showErrorMessage(`Error: ${error instanceof Error ? error.message : String(error)}`);
        }
    });

    context.subscriptions.push(disposable);
}

function generateInstructions(spec: any): string {
    return `# Project: ${spec.title}

## Overview
${spec.description}

## Requirements

### Key Features
${spec.features.map((f: any) => `- ${f.name}: ${f.description} (Priority: ${f.priority})`).join('\n')}

### Technical Stack
${spec.technologies.map((t: any) => `- ${t.name}: ${t.purpose}`).join('\n')}

### Architecture
Type: ${spec.architecture.type}

Components:
${spec.architecture.components.map((c: any) => 
    `- ${c.name}: ${c.purpose}\n  Interactions: ${c.interactions.join('; ')}`
).join('\n')}

## Implementation Plan
${spec.implementationPlan.map((phase: any, i: number) => 
    `Phase ${i + 1}: ${phase.phase} (${phase.duration})\n` +
    phase.tasks.map((task: any) => `  - ${task.name} (${task.duration})`).join('\n')
).join('\n')}

## Development Guidelines

1. Follow modern development practices and patterns
2. Implement proper error handling and logging
3. Write clean, maintainable, and well-documented code
4. Include appropriate tests for all components
5. Consider scalability and performance in the implementation

Please generate the project structure and implementation based on these specifications.`;
}

export function deactivate() {} 