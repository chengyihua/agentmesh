export async function solvePoW(nonce: string, difficulty: number = 4): Promise<string> {
    let solution = 0;
    const prefix = "0".repeat(difficulty);
    
    while (true) {
        const solutionStr = solution.toString();
        const data = new TextEncoder().encode(nonce + solutionStr);
        const hashBuffer = await window.crypto.subtle.digest("SHA-256", data);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hashHex = hashArray.map(b => b.toString(16).padStart(2, "0")).join("");
        
        if (hashHex.startsWith(prefix)) {
            return solutionStr;
        }
        solution++;
        
        // Safety break to prevent infinite loops in testing
        // Difficulty 4 should be found within ~65k attempts on average (16^4 = 65536)
        if (solution > 1000000) {
            throw new Error("PoW solution not found within reasonable attempts");
        }
    }
}
