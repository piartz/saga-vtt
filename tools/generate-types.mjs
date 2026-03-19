#!/usr/bin/env node
/**
 * Code generator: Reads protocol.json schema and generates TypeScript types
 *
 * Usage: node tools/generate-types.mjs
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SCHEMA_PATH = path.join(__dirname, '../schemas/protocol.json');
const OUTPUT_PATH = path.join(__dirname, '../apps/web/src/protocol.generated.ts');

function jsonSchemaTypeToTS(schema, definitions) {
  if (schema.$ref) {
    const refName = schema.$ref.split('/').pop();
    return refName;
  }

  if (schema.oneOf) {
    return schema.oneOf.map(s => jsonSchemaTypeToTS(s, definitions)).join(' | ');
  }

  if (schema.type === 'string') {
    if (schema.enum) {
      return schema.enum.map(v => `"${v}"`).join(' | ');
    }
    return 'string';
  }

  if (schema.type === 'integer' || schema.type === 'number') {
    return 'number';
  }

  if (schema.type === 'boolean') {
    return 'boolean';
  }

  if (schema.type === 'null') {
    return 'null';
  }

  if (schema.type === 'array') {
    const itemType = jsonSchemaTypeToTS(schema.items, definitions);
    return `${itemType}[]`;
  }

  if (schema.type === 'object') {
    const props = schema.properties || {};
    const required = schema.required || [];

    const lines = Object.entries(props).map(([key, propSchema]) => {
      const isRequired = required.includes(key);
      const tsType = jsonSchemaTypeToTS(propSchema, definitions);
      return `  ${key}${isRequired ? '' : '?'}: ${tsType};`;
    });

    return `{\n${lines.join('\n')}\n}`;
  }

  return 'unknown';
}

function generateDefinitions(definitions) {
  const lines = [];

  for (const [name, schema] of Object.entries(definitions)) {
    if (schema.type === 'string' && schema.enum) {
      // Generate string literal union type
      const values = schema.enum.map(v => `"${v}"`).join(' | ');
      lines.push(`export type ${name} = ${values};`);
      lines.push('');
    } else if (schema.type === 'object') {
      // Generate interface
      const props = schema.properties || {};
      const required = schema.required || [];

      lines.push(`export interface ${name} {`);
      for (const [key, propSchema] of Object.entries(props)) {
        const isRequired = required.includes(key);
        const tsType = jsonSchemaTypeToTS(propSchema, definitions);
        lines.push(`  ${key}${isRequired ? '' : '?'}: ${tsType};`);
      }
      lines.push('}');
      lines.push('');
    }
  }

  return lines.join('\n');
}

function generateCommands(commands, definitions) {
  const lines = [];

  lines.push('// Command Payloads');
  lines.push('');

  for (const [name, commandSchema] of Object.entries(commands)) {
    const payloadTypeName = `${name}Payload`;
    const tsType = jsonSchemaTypeToTS(commandSchema.payload, definitions);

    // Check if payload is empty (no properties)
    const props = commandSchema.payload.properties || {};
    const isEmpty = Object.keys(props).length === 0;

    if (isEmpty) {
      // Empty payload
      lines.push(`export type ${payloadTypeName} = Record<string, never>;`);
    } else {
      lines.push(`export type ${payloadTypeName} = ${tsType};`);
    }
    lines.push('');
  }

  // Generate command type union
  const commandNames = Object.keys(commands).map(name => `"${name}"`).join(' | ');
  lines.push(`export type CommandType = ${commandNames};`);
  lines.push('');

  // Generate command envelope interface
  lines.push('export interface CommandEnvelope {');
  lines.push('  kind: "COMMAND";');
  lines.push('  type: CommandType;');
  lines.push('  client_msg_id: string;');
  lines.push('  payload: unknown;');
  lines.push('}');
  lines.push('');

  return lines.join('\n');
}

function generateEvents(events, definitions) {
  const lines = [];

  lines.push('// Event Payloads');
  lines.push('');

  for (const [name, eventSchema] of Object.entries(events)) {
    const payloadTypeName = `${name}Payload`;
    const tsType = jsonSchemaTypeToTS(eventSchema.payload, definitions);

    // Check if payload is empty (no properties)
    const props = eventSchema.payload.properties || {};
    const isEmpty = Object.keys(props).length === 0;

    if (isEmpty) {
      // Empty payload
      lines.push(`export type ${payloadTypeName} = Record<string, never>;`);
    } else {
      lines.push(`export type ${payloadTypeName} = ${tsType};`);
    }
    lines.push('');
  }

  // Generate event type union
  const eventNames = Object.keys(events).map(name => `"${name}"`).join(' | ');
  lines.push(`export type EventType = ${eventNames};`);
  lines.push('');

  // Generate event envelope interface
  lines.push('export interface EventEnvelope {');
  lines.push('  kind: "EVENT";');
  lines.push('  type: EventType;');
  lines.push('  seq: number;');
  lines.push('  server_time: string;');
  lines.push('  actor_player_id?: string;');
  lines.push('  payload: unknown;');
  lines.push('}');
  lines.push('');

  return lines.join('\n');
}

function main() {
  console.log('🔨 Generating TypeScript types from protocol schema...');

  // Read schema
  const schemaContent = fs.readFileSync(SCHEMA_PATH, 'utf-8');
  const schema = JSON.parse(schemaContent);

  // Generate code
  const header = `/**
 * AUTO-GENERATED FILE - DO NOT EDIT
 *
 * This file is generated from schemas/protocol.json
 * Run 'pnpm generate-types' to regenerate
 */

`;

  const definitions = generateDefinitions(schema.definitions);
  const commands = generateCommands(schema.commands, schema.definitions);
  const events = generateEvents(schema.events, schema.definitions);

  const output = header + definitions + '\n' + commands + '\n' + events;

  // Write output
  fs.writeFileSync(OUTPUT_PATH, output, 'utf-8');

  console.log(`✅ Generated TypeScript types: ${OUTPUT_PATH}`);
  console.log(`   - ${Object.keys(schema.definitions).length} definitions`);
  console.log(`   - ${Object.keys(schema.commands).length} commands`);
  console.log(`   - ${Object.keys(schema.events).length} events`);
}

main();
