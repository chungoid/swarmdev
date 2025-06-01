#!/usr/bin/env node

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

// Define the schema using ZodRawShape format for the tool parameters
const thinkingStepSchema = {
  thought: z.string().describe('Your current thinking step'),
  nextThoughtNeeded: z.boolean().describe('Whether another thought step is needed'),
  thoughtNumber: z.number().int().min(1).describe('Current thought number'),
  totalThoughts: z.number().int().min(1).describe('Estimated total thoughts needed'),
  isRevision: z.boolean().optional().describe('Whether this revises previous thinking'),
  revisesThought: z.number().int().min(1).optional().describe('Which thought is being reconsidered'),
  branchFromThought: z.number().int().min(1).optional().describe('Branching point thought number'),
  branchId: z.string().optional().describe('Branch identifier'),
  needsMoreThoughts: z.boolean().optional().describe('If more thoughts are needed')
};

interface ThinkingStep {
  thought: string;
  nextThoughtNeeded: boolean;
  thoughtNumber: number;
  totalThoughts: number;
  isRevision?: boolean;
  revisesThought?: number;
  branchFromThought?: number;
  branchId?: string;
  needsMoreThoughts?: boolean;
}

class SequentialThinkingServer {
  private server: McpServer;

  constructor() {
    this.server = new McpServer({
      name: 'sequential-thinking',
      version: '1.0.0',
    });

    this.setupHandlers();
  }

  private setupHandlers() {
    // Register the sequential thinking tool using the modern API
    this.server.tool(
      'sequential_thinking',
      'Advanced reasoning through sequential thoughts with revision and branching capabilities',
      thinkingStepSchema,
      async (args: ThinkingStep) => {
        // Process the thinking step
        const result = {
          thoughtProcessed: true,
          thoughtNumber: args.thoughtNumber,
          totalThoughts: args.totalThoughts,
          continueThinking: args.nextThoughtNeeded,
          reasoning: `Processed thought ${args.thoughtNumber}/${args.totalThoughts}: ${args.thought.substring(0, 100)}...`,
          guidance: this.generateGuidance(args)
        };

        return {
          content: [
            {
              type: 'text' as const,
              text: JSON.stringify(result, null, 2)
            }
          ]
        };
      }
    );
  }

  private generateGuidance(step: ThinkingStep): string {
    if (step.isRevision) {
      return `Revision mode: Reconsidering thought ${step.revisesThought}. Consider alternative approaches.`;
    }
    
    if (step.branchFromThought) {
      return `Branching from thought ${step.branchFromThought}. Explore parallel reasoning path.`;
    }
    
    if (step.thoughtNumber >= step.totalThoughts && step.nextThoughtNeeded) {
      return 'Extending beyond initial estimate. Ensure additional thoughts add value.';
    }
    
    if (step.thoughtNumber < step.totalThoughts) {
      return 'Continue systematic reasoning. Build on previous insights.';
    }
    
    return 'Consider if reasoning is complete or needs further development.';
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

const server = new SequentialThinkingServer();
server.run().catch(console.error); 