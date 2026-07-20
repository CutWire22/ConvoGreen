# ConvoGreen

An efficient, local multi-agent AI orchestration and calibration harness designed for local setups. 
(Because let's face it, loading and unloading models is the smarter way of having multiple models in same chat.)

ConvoGreen allows two local LLM profiles (e.g., Qwen, Gemma, Llama) to interact dynamically with a human user or engage in an automated continuous debate without causing Out-Of-Memory (OOM) errors.

## Key Features

* **Sequential VRAM Swapping:** Automatically loads and unloads models between turns to maximize local VRAM efficiency.
* **Isolated Turn Attribution:** Dynamically formats historical context so models maintain distinct identities without context bleeding or persona duplication.
* **Continuous Debate Mode:** Enables two local models to chat back-and-forth indefinitely in an automated feedback loop.
* **OpenAI API Standard:** Connects directly to local completion servers (Ollama, vLLM, LM Studio, KoboldCPP).
* **Attempt at Premium Brand Industrial Aesthetic:** Clean, low-contrast dark charcoal and anodized emerald UI. I wanted dark-mode without it looking like yet another dark mode. Easy on the eye.
* **Independent RAG system:** Each models have their own section for documents which would allow for creative use. (One model has script 1 while other has script 2)

## Some Use Case Ideas

1) Sandbox between two different models or personas.
2) Having models challenge each other and test logic or fact check one another. 
3) Having models collaborate as a group or with each other.
4) Test out effects of Quantization or different model sizes to see how often the better model catches the worse model's mistakes. (8bit model vs 4bit model) or (27B vs 9B)
5) Use separate RAG context panels to run "blind" scenarios—forcing models to deduce, roleplay, or problem-solve using secret information the other side can't see.
6) Not really an idea, just comment. It's 2 models in the same chat window. Use it how you want. It's made simple for a reason.

## Research & Theoretical Foundations

ConvoGreen's multi-agent architecture draws inspiration from established research in multi-agent consensus and adversarial debate:

* **[Multiagent Debate (Du et al., 2023)](https://arxiv.org/abs/2305.14325):** Demonstrates that multi-turn LLM cross-examination significantly reduces hallucinations and improves logical accuracy.
* **[AI Safety via Debate (Irving et al., OpenAI, 2018)](https://arxiv.org/abs/1805.00899):** Shows how competitive agent dialogue allows human operators to easily evaluate truth and spot logical flaws.
* **[Generative Adversarial Networks (Goodfellow et al., 2014)](https://arxiv.org/abs/1406.2661):** The foundational zero-sum competitive architecture for continuous output refinement.

## Quick Start

1. Clone the repository:
   ```bash
   git clone [https://github.com/CutWire22/ConvoGreen.git](https://github.com/CutWire22/ConvoGreen.git)
   cd ConvoGreen
   
