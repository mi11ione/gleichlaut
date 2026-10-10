# Chat template: the GGUF's embedded template against the official Apertus template

Checked on 10 Oct 2026, without running a model. Question (from an Apertus-team juror): which turns does the chat
template add before our one user message, and is the template embedded in the shipped GGUF the official one?

## Sources

| Template | Source (anonymous HTTP) | Revision | sha256 of the template text (UTF-8) |
|---|---|---|---|
| embedded in the shipped Q8_0 GGUF | `andreasmartin/apertus-v1.5-8b-text-Q8_0-GGUF`, file `apertus-v1.5-8b-text-q8_0.gguf`, GGUF v3 key `tokenizer.chat_template`, read with two HTTP Range requests (bytes 0 to 8,388,607; the 41 metadata keys end at byte 7,883,904) | `2028c3184c0fa060b4259b33ee25e836da6896e5` | `d23af2850029e9df88bb017e06e0c14a0462604588f1dbe4f519cdfac3e260e0` |
| official | `swiss-ai/Apertus-v1.5-8B`. The files `chat_template.jinja` and `tokenizer_config.json` are gated (HTTP 401 without a login), but the public model-info API returns the template (`/api/models/swiss-ai/Apertus-v1.5-8B/revision/<sha>?expand[]=config`, field `config.chat_template_jinja`) | `a411d838600baf0e3635a3daf66fb7c55fc97bb6` (24 Jul 2026) | `d23af285…` (the same) |
| text-only extraction (step 2 of the GGUF chain) | `andreasmartin/apertus-v1.5-8b-text`, same API, `chat_template_jinja` and `tokenizer_config.chat_template` | `c0e7eeb69c55c7810c91de3a1f97dde4d4b14b01` | `d23af285…` (the same, both fields) |
| embedded in the Q4_K_M GGUF (8 GiB option) | `Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF`, `apertus-v1.5-8b-text-q4_k_m.gguf`, Range requests as above | `248ec68a63e219e3f061e4c946fc8a20d63b9975` | `d23af285…` (the same) |
| official 70B, for reference | `swiss-ai/Apertus-v1.5-70B`, same API | `59e744e313e967811aefabde3732609b64201acc` | `d23af285…` (the same) |

Saved copies: [`chat_template_gguf_q8_0.jinja`](chat_template_gguf_q8_0.jinja) and
[`chat_template_official_apertus-v1.5-8b.jinja`](chat_template_official_apertus-v1.5-8b.jinja) (16,614 bytes each).

## Diff

None. All five templates are byte-identical (16,614 characters, one sha256). One difference lies outside the template:
the official `tokenizer_config.json` names `eos_token` `</s>`, while the extraction and both GGUFs use
`<|assistant_end|>` (GGUF `tokenizer.ggml.eos_token_id` 68; `bos_token_id` 1 = `<s>`). The template never reads
`eos_token`, so the rendered prompt is the same either way. The difference only decides where generation stops:
llama-cpp-python stops at token 68, the end of the assistant turn.

## How llama-cpp-python 0.3.35 renders it

`Llama.__init__` (`llama_cpp/llama.py`, tag v0.3.35) finds `tokenizer.chat_template` in the GGUF metadata. No
built-in format matches, so it uses `Jinja2ChatFormatter` (`llama_chat_format.py`): a jinja2
`ImmutableSandboxedEnvironment` with `trim_blocks`, `lstrip_blocks`, the `loopcontrols` and `generation` extensions and
a `tojson` filter. `create_chat_completion` renders it with exactly these variables: `messages`, `bos_token` (`<s>`),
`eos_token` (`<|assistant_end|>`), `raise_exception`, `add_generation_prompt=True`, `functions=None`,
`function_call=None`, `tools=None`, `tool_choice=None`, `strftime_now`. No date and no `enable_thinking` are passed.
The rendered text is tokenized with `add_bos=False, special=True` (`added_special=True`), so the template's own
`{{ bos_token }}` is the only BOS. In the template, `tools=None` renders "Tool Capabilities: disabled", and the
undefined `enable_thinking` renders "Deliberation: disabled". That is the same output as `enable_thinking=False`,
which our MLX research scripts passed.

## One recorded request, rendered

The request is the first call for item `wb000-fr` of the Q8_0 rerun (`score.RUNS["q8_0_rerun"]`, model
`gguf:q8_0.gguf`, max_tokens 401). We rebuilt the prompt with the frozen pipeline and it hit the recorded cache entry
`data/cache/responses_8b/q8_0/1c/1ca593e76fef1df72e8df4b1dbfafed7205fe4257df85cb7212d54bb7d0429ec.json` (recorded
`prompt_tokens` 591), so this is the prompt that was sent. We rendered it through both templates with jinja2 3.1.6
(the version pinned in the offline image) and the settings above. The two renderings are identical: 2,308 characters,
sha256 `bee3eaa1ca6f13ff0882f825562195dd6e10afc72b81fa9896d44770166d9b25`. The user content (1,954 characters) is
shortened here:

```
<s><|system_start|>You are Apertus 1.5 Omni, a multimodal assistant developed by the Swiss AI Initiative. Extended from Apertus 1 via continued pretraining, you understand images and audio and respond in text.<|system_end|><|developer_start|>Deliberation: disabled
Tool Capabilities: disabled<|developer_end|><|user_start|>A Swiss reimbursement limitation (Spezialitätenliste, BAG) was amended in German. Apply exactly the same amendment to the French version.
[... 1,723 characters: German old/new, the change list, French old ...]
Output only the amended French text, nothing else.<|user_end|><|assistant_start|>
```

So two turns come before our user message:

- system: `You are Apertus 1.5 Omni, a multimodal assistant developed by the Swiss AI Initiative. Extended from Apertus 1 via continued pretraining, you understand images and audio and respond in text.` (the template's default, because we send no system message)
- developer: `Deliberation: disabled\nTool Capabilities: disabled` (always present)

## Conclusion

The chat template embedded in both shipped GGUFs is byte-identical to the official `swiss-ai/Apertus-v1.5-8B`
template (and to the official 70B one); the only difference is outside the template (the end-of-sequence token), and
it does not change the prompt, so no re-run is needed. For our one user message the template adds the default system
turn "You are Apertus 1.5 Omni, a multimodal assistant developed by the Swiss AI Initiative. Extended from Apertus 1
via continued pretraining, you understand images and audio and respond in text." and the developer turn
"Deliberation: disabled / Tool Capabilities: disabled", then opens the assistant turn. For the 70B we cannot inspect
the template Public AI's server applies; we only know the official 70B template is this same one.
