export type DigestFn = (algo: AlgorithmIdentifier | string, data: BufferSource) => Promise<ArrayBuffer>;

export interface PowOptions {
  difficulty?: number;
  maxAttempts?: number;
  timeoutMs?: number;
  signal?: AbortSignal;
  yieldEvery?: number; // Yield to event loop every N attempts
  progress?: (attempt: number) => void;
  digest?: DigestFn; // Injectable digest for SSR/Test environments
}

export async function solvePoW(nonce: string, difficulty: number): Promise<string>;
export async function solvePoW(nonce: string, options?: PowOptions): Promise<string>;
export async function solvePoW(
  nonce: string,
  optionsOrDifficulty: number | PowOptions = 4
): Promise<string> {
  let options: PowOptions;
  
  if (typeof optionsOrDifficulty === 'number') {
    options = { difficulty: optionsOrDifficulty };
  } else {
    options = optionsOrDifficulty || {};
  }

  const {
    difficulty = 4,
    maxAttempts = 1_000_000,
    timeoutMs,
    signal,
    yieldEvery = 500,
    progress,
    digest,
  } = options;

  if (!Number.isInteger(difficulty) || difficulty < 0 || difficulty > 8) {
    throw new Error("Invalid difficulty: expected integer 0~8");
  }
  if (!Number.isInteger(maxAttempts) || maxAttempts <= 0) {
    throw new Error("Invalid maxAttempts");
  }

  const prefix = "0".repeat(difficulty);
  const doDigest: DigestFn = digest ?? (async (algo, data) => {
    const subtle = (globalThis as any)?.crypto?.subtle;
    if (!subtle) throw new Error("WebCrypto not available; provide a digest implementation in PowOptions");
    return subtle.digest(algo as any, data);
  });

  const start = Date.now();
  let attempt = 0;

  const checkAbort = () => {
    if (signal?.aborted) {
        // Use standard AbortError if available, otherwise generic Error
        if (typeof DOMException !== 'undefined') {
            throw new DOMException("Aborted", "AbortError");
        }
        const err = new Error("Aborted");
        err.name = "AbortError";
        throw err;
    }
    if (timeoutMs && Date.now() - start > timeoutMs) throw new Error("PoW timed out");
  };

  while (attempt < maxAttempts) {
    // Check abort/timeout periodically inside the loop to avoid too frequent checks if needed,
    // but doing it every iteration is safer for immediate cancellation.
    // Optimization: check every `yieldEvery` or a smaller batch size if performance is critical.
    // For now, checking every iteration is fine as it's just a boolean/time check.
    if (attempt % 100 === 0) checkAbort();

    const solutionStr = String(attempt);
    const data = new TextEncoder().encode(nonce + solutionStr);
    const hashBuffer = await doDigest("SHA-256", data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, "0")).join("");

    if (hashHex.startsWith(prefix)) return solutionStr;

    attempt++;
    if (attempt % yieldEvery === 0) {
      progress?.(attempt);
      // Yield to main thread to prevent blocking UI
      await new Promise(r => setTimeout(r, 0));
    }
  }

  throw new Error("PoW solution not found within reasonable attempts");
}
