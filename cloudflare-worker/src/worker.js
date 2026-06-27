/**
 * OpenMontage AI proxy — OpenAI-compatible surface over Cloudflare Workers AI.
 *
 * Endpoints:
 *   GET  /                       health check
 *   GET  /v1/models              list mapped models
 *   POST /v1/images/generations  OpenAI-style image gen -> { data: [{ b64_json }] }
 *   POST /v1/chat/completions    OpenAI-style chat -> proxied to a Workers AI LLM
 *
 * Optional auth: if the PROXY_SECRET secret is set, requests must send
 *   Authorization: Bearer <PROXY_SECRET>
 */

const IMAGE_MODELS = {
  "flux-schnell": "@cf/black-forest-labs/flux-1-schnell",
  "flux": "@cf/black-forest-labs/flux-1-schnell",
  "sdxl": "@cf/stabilityai/stable-diffusion-xl-base-1.0",
  "sdxl-lightning": "@cf/bytedance/stable-diffusion-xl-lightning",
  "dreamshaper": "@cf/lykon/dreamshaper-8-lcm",
};

const CHAT_MODELS = {
  "default": "@cf/meta/llama-3.1-8b-instruct",
  "llama-3.1-8b": "@cf/meta/llama-3.1-8b-instruct",
  "llama-3.3-70b": "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
};

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", "access-control-allow-origin": "*" },
  });
}

function authOk(request, env) {
  if (!env.PROXY_SECRET) return true; // open if no secret configured
  const h = request.headers.get("authorization") || "";
  return h === `Bearer ${env.PROXY_SECRET}`;
}

function parseSize(size) {
  if (!size || typeof size !== "string" || !size.includes("x")) return [1024, 1024];
  const [w, h] = size.split("x").map((n) => parseInt(n, 10));
  return [w || 1024, h || 1024];
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/") {
      return json({ ok: true, service: "openmontage-ai", endpoints: ["/v1/images/generations", "/v1/chat/completions", "/v1/models"] });
    }

    if (request.method === "GET" && url.pathname === "/v1/models") {
      const data = [...Object.keys(IMAGE_MODELS), ...Object.keys(CHAT_MODELS)].map((id) => ({ id, object: "model" }));
      return json({ object: "list", data });
    }

    if (!authOk(request, env)) return json({ error: { message: "unauthorized" } }, 401);

    // ---- Images ----
    if (request.method === "POST" && url.pathname === "/v1/images/generations") {
      let body;
      try { body = await request.json(); } catch { return json({ error: { message: "invalid json" } }, 400); }
      const model = IMAGE_MODELS[body.model] || IMAGE_MODELS["flux-schnell"];
      const [width, height] = parseSize(body.size);
      const inputs = { prompt: body.prompt, width, height };
      if (body.seed != null) inputs.seed = body.seed;
      if (body.negative_prompt) inputs.negative_prompt = body.negative_prompt;
      if (body.steps) inputs.steps = body.steps;

      try {
        const out = await env.AI.run(model, inputs);
        // FLUX returns { image: <base64> }; SD models may return a ReadableStream of bytes.
        let b64;
        if (out && typeof out === "object" && typeof out.image === "string") {
          b64 = out.image;
        } else if (out instanceof ReadableStream || out instanceof ArrayBuffer || out instanceof Uint8Array) {
          const buf = out instanceof ReadableStream ? await new Response(out).arrayBuffer() : out;
          const bytes = new Uint8Array(buf instanceof ArrayBuffer ? buf : buf.buffer || buf);
          let bin = ""; for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
          b64 = btoa(bin);
        } else {
          return json({ error: { message: "unexpected model output", model } }, 502);
        }
        return json({ created: Math.floor(Date.now() / 1000), data: [{ b64_json: b64 }], model });
      } catch (e) {
        return json({ error: { message: String(e && e.message || e), model } }, 502);
      }
    }

    // ---- Chat ----
    if (request.method === "POST" && url.pathname === "/v1/chat/completions") {
      let body;
      try { body = await request.json(); } catch { return json({ error: { message: "invalid json" } }, 400); }
      const model = CHAT_MODELS[body.model] || CHAT_MODELS["default"];
      try {
        const out = await env.AI.run(model, { messages: body.messages || [], max_tokens: body.max_tokens || 1024 });
        const content = (out && (out.response ?? out.result?.response)) || "";
        return json({
          id: "chatcmpl-" + Date.now(),
          object: "chat.completion",
          created: Math.floor(Date.now() / 1000),
          model,
          choices: [{ index: 0, message: { role: "assistant", content }, finish_reason: "stop" }],
        });
      } catch (e) {
        return json({ error: { message: String(e && e.message || e), model } }, 502);
      }
    }

    return json({ error: { message: "not found" } }, 404);
  },
};
