#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import * as fs from 'fs';
import * as path from 'path';

interface MemoryEntry {
  id: string;
  key: string;
  value: any;
  timestamp: string;
  metadata?: Record<string, any>;
}

class MemoryServer {
  private server: Server;
  private memoryDir: string;
  private memoryData: Map<string, MemoryEntry> = new Map();

  constructor() {
    this.memoryDir = process.env.MEMORY_DIR || '/tmp/mcp-memory';
    this.ensureMemoryDir();
    this.loadExistingMemory();

    this.server = new Server(
      {
        name: 'memory',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private ensureMemoryDir() {
    if (!fs.existsSync(this.memoryDir)) {
      fs.mkdirSync(this.memoryDir, { recursive: true });
    }
  }

  private loadExistingMemory() {
    try {
      const memoryFile = path.join(this.memoryDir, 'memory.json');
      if (fs.existsSync(memoryFile)) {
        const data = JSON.parse(fs.readFileSync(memoryFile, 'utf8'));
        this.memoryData = new Map(Object.entries(data));
      }
    } catch (error) {
      console.error('Error loading existing memory:', error);
    }
  }

  private saveMemory() {
    try {
      const memoryFile = path.join(this.memoryDir, 'memory.json');
      const data = Object.fromEntries(this.memoryData);
      fs.writeFileSync(memoryFile, JSON.stringify(data, null, 2));
    } catch (error) {
      console.error('Error saving memory:', error);
    }
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'store_memory',
            description: 'Store information in persistent memory',
            inputSchema: {
              type: 'object',
              properties: {
                key: {
                  type: 'string',
                  description: 'Unique key for the memory entry'
                },
                value: {
                  description: 'Value to store (can be any type)'
                },
                metadata: {
                  type: 'object',
                  description: 'Optional metadata for the entry'
                }
              },
              required: ['key', 'value']
            }
          },
          {
            name: 'retrieve_memory',
            description: 'Retrieve information from persistent memory',
            inputSchema: {
              type: 'object',
              properties: {
                key: {
                  type: 'string',
                  description: 'Key of the memory entry to retrieve'
                }
              },
              required: ['key']
            }
          },
          {
            name: 'list_memory',
            description: 'List all memory keys or search by pattern',
            inputSchema: {
              type: 'object',
              properties: {
                pattern: {
                  type: 'string',
                  description: 'Optional pattern to filter keys'
                }
              }
            }
          },
          {
            name: 'delete_memory',
            description: 'Delete a memory entry',
            inputSchema: {
              type: 'object',
              properties: {
                key: {
                  type: 'string',
                  description: 'Key of the memory entry to delete'
                }
              },
              required: ['key']
            }
          }
        ]
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      switch (request.params.name) {
        case 'store_memory':
          return this.storeMemory(request.params.arguments as any);
        case 'retrieve_memory':
          return this.retrieveMemory(request.params.arguments as any);
        case 'list_memory':
          return this.listMemory(request.params.arguments as any);
        case 'delete_memory':
          return this.deleteMemory(request.params.arguments as any);
        default:
          throw new Error(`Unknown tool: ${request.params.name}`);
      }
    });
  }

  private async storeMemory(args: { key: string; value: any; metadata?: any }) {
    const entry: MemoryEntry = {
      id: Date.now().toString(),
      key: args.key,
      value: args.value,
      timestamp: new Date().toISOString(),
      metadata: args.metadata
    };

    this.memoryData.set(args.key, entry);
    this.saveMemory();

    return {
      content: [
        {
          type: 'text',
          text: `Stored memory entry with key: ${args.key}`
        }
      ]
    };
  }

  private async retrieveMemory(args: { key: string }) {
    const entry = this.memoryData.get(args.key);
    
    if (!entry) {
      return {
        content: [
          {
            type: 'text',
            text: `No memory entry found for key: ${args.key}`
          }
        ]
      };
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            key: entry.key,
            value: entry.value,
            timestamp: entry.timestamp,
            metadata: entry.metadata
          }, null, 2)
        }
      ]
    };
  }

  private async listMemory(args: { pattern?: string }) {
    let keys = Array.from(this.memoryData.keys());
    
    if (args.pattern) {
      const regex = new RegExp(args.pattern, 'i');
      keys = keys.filter(key => regex.test(key));
    }

    const entries = keys.map(key => {
      const entry = this.memoryData.get(key)!;
      return {
        key: entry.key,
        timestamp: entry.timestamp,
        hasMetadata: !!entry.metadata
      };
    });

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({
            total: entries.length,
            entries: entries
          }, null, 2)
        }
      ]
    };
  }

  private async deleteMemory(args: { key: string }) {
    const existed = this.memoryData.has(args.key);
    this.memoryData.delete(args.key);
    
    if (existed) {
      this.saveMemory();
    }

    return {
      content: [
        {
          type: 'text',
          text: existed 
            ? `Deleted memory entry with key: ${args.key}`
            : `No memory entry found for key: ${args.key}`
        }
      ]
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
  }
}

const server = new MemoryServer();
server.run().catch(console.error); 