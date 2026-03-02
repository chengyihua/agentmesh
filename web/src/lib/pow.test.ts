import { describe, it } from 'node:test';
import assert from 'node:assert';
import crypto from 'node:crypto';
// @ts-ignore
import { solvePoW, DigestFn } from './pow';

// Polyfill-like digest function for Node.js
const nodeDigest: DigestFn = async (algo, data) => {
    // Simplified check
    if (algo !== 'SHA-256' && (typeof algo !== 'object' || (algo as any).name !== 'SHA-256')) {
         // Just proceed for test simplicity or throw
    }
    
    const hash = crypto.createHash('sha256');
    // Handle both ArrayBuffer and ArrayBufferView
    const view = ArrayBuffer.isView(data) 
        ? new Uint8Array(data.buffer, data.byteOffset, data.byteLength)
        : new Uint8Array(data as ArrayBuffer);
        
    hash.update(view);
    const buffer = hash.digest();
    // Convert Buffer to ArrayBuffer
    return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
};

describe('solvePoW', () => {
    it('should solve PoW with custom digest', async () => {
        const nonce = 'test-nonce-' + Date.now();
        const difficulty = 1; 
        // Note: We are testing the new API signature here
        const result = await solvePoW(nonce, { 
            difficulty, 
            digest: nodeDigest,
            maxAttempts: 1000
        });
        
        const solutionStr = result;
        const data = new TextEncoder().encode(nonce + solutionStr);
        // Verify manually
        const hashBuffer = await nodeDigest("SHA-256", data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
        
        assert.ok(hashHex.startsWith('0'.repeat(difficulty)), `Hash ${hashHex} should start with ${'0'.repeat(difficulty)}`);
    });

    it('should abort with AbortSignal', async () => {
        const controller = new AbortController();
        const promise = solvePoW('test-abort', { 
            difficulty: 8, // High difficulty
            signal: controller.signal,
            digest: nodeDigest
        });
        
        // Abort immediately
        setTimeout(() => controller.abort(), 10);
        
        try {
            await promise;
            assert.fail('Should have aborted');
        } catch (e: any) {
            assert.ok(e.name === 'AbortError' || e.message === 'Aborted', `Expected AbortError, got ${e.message}`);
        }
    });

    it('should timeout', async () => {
        try {
            await solvePoW('test-timeout', { 
                difficulty: 8, 
                timeoutMs: 50, // Short timeout
                digest: nodeDigest
            });
            assert.fail('Should have timed out');
        } catch (e: any) {
             assert.ok(e.message.includes('timed out'), `Expected timeout error, got ${e.message}`);
        }
    });

    it('should validate difficulty', async () => {
        try {
            await solvePoW('test', { difficulty: -1, digest: nodeDigest });
            assert.fail('Should fail with invalid difficulty');
        } catch (e: any) {
            assert.ok(e.message.includes('Invalid difficulty'), 'Should throw invalid difficulty error');
        }
    });
});
