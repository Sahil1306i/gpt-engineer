# GPT Engineer

[![Discord Follow](https://dcbadge.vercel.app/api/server/8tcDQ89Ej2?style=flat)](https://discord.gg/8tcDQ89Ej2)
[![GitHub Repo stars](https://img.shields.io/github/stars/AntonOsika/gpt-engineer?style=social)](https://github.com/AntonOsika/gpt-engineer)
[![Twitter Follow](https://img.shields.io/twitter/follow/antonosika?style=social)](https://twitter.com/AntonOsika)


**Specify what you want it to build, the AI asks for clarification, and then builds it.**

GPT Engineer is made to be easy to adapt, extend, and make your agent learn how you want your code to look. It generates an entire codebase based on a prompt.

[Demo](https://twitter.com/antonosika/status/1667641038104674306)

## Project philosophy

- Simple to get value
- Flexible and easy to add new own "AI steps". See `steps.py`.
- Incrementally build towards a user experience of:
  1. high level prompting
  2. giving feedback to the AI that it will remember over time
- Fast handovers back and forth between AI and human
- Simplicity, all computation is "resumable" and persisted to the filesystem

## Usage

Choose either **stable** or **development**.

For **stable** release:

- `python -m pip install gpt-engineer`

For **development**:
- `git clone https://github.com/AntonOsika/gpt-engineer.git`
- `cd gpt-engineer`
- `python -m pip install -e .`
  - (or: `make install && source venv/bin/activate` for a venv)

**API Key**
Either just:
- `export OPENAI_API_KEY=[your api key]`

Or:
- Create a copy of `.env.template` named `.env`
- Add your OPENAI_API_KEY in .env

Check the [Windows README](./WINDOWS_README.md) for windows usage.

**Running**

- Create an empty folder. If inside the repo, you can run:
  - `cp -r projects/example/ projects/my-new-project`
- Fill in the `prompt` file in your new folder
- `gpt-engineer projects/my-new-project`
  - (Note, `gpt-engineer --help` lets you see all available options. For example `--steps use_feedback` lets you improve/fix code in a project)

By running gpt-engineer you agree to our [terms](https://github.com/AntonOsika/gpt-engineer/blob/main/TERMS_OF_USE.md).

**Azure OpenAI Service**

You'll set your Azure OpenAI KEY 1 or KEY 2 as:
- `export OPENAI_API_KEY=[your api key]`

Then you call `gpt-engineer` with your service endpoint `--azure https://aoi-resource-name.openai.azure.com` and set your deployment name (which you created in the Azure AI Studio) as the model name. Example: `gpt-engineer --azure https://myairesource.openai.azure.com ./projects/example/ my-gpt4-deployment-name`

**Results**

Check the generated files in `projects/my-new-project/workspace`

**Alternatives**

You can check [Docker instructions](docker/README.md) to use Docker, or simply
do everything in your browser:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/AntonOsika/gpt-engineer/codespaces)

## Features

You can specify the "identity" of the AI agent by editing the files in the `preprompts` folder.

Editing the `preprompts`, and evolving how you write the project prompt, is how you make the agent remember things between projects.

Each step in `steps.py` will have its communication history with GPT4 stored in the logs folder, and can be rerun with `scripts/rerun_edited_message_logs.py`.

### Running with open source models

You can use gpt-engineer with open source models by using an OpenAI compatible API, such as the one offered by the [text-generator-ui extension `openai`](https://github.com/oobabooga/text-generation-webui/blob/main/extensions/openai/README.md). This can easily be setup with [TheBloke's Runpod template](https://www.runpod.io/console/gpu-secure-cloud?template=f1pf20op0z).

To do so, first set up the API according to the instructions linked above. Then you need to go into the text-generation-webui, go to settings, check the `openai` extension, save. You then need to expose TCP port 5001 in your Runpod config, which will give it an exposed TCP port something like 40125. Then restart your Runpod, and check that the API is live by browsing: http://<public ip>:<port>/v1/models

Then, as an example we can now run it with WizardCoder-Python-34B hosted on Runpod: `OPENAI_API_BASE=http://<host>:<port>/v1 python -m gpt_engineer.main benchmark/pomodoro_timer --steps benchmark TheBloke_WizardCoder-Python-34B-V1.0-GPTQ`

Check your Runpod dashboard for the host and (exposed TCP) port, mine was something like 40125.

## Vision
The gpt-engineer community is building the **open platform for devs to tinker with and build their personal code-generation toolbox**.

If you are interested in contributing to this, we would be interested in having you.

If you want to see our broader ambitions, check out the [roadmap](https://github.com/AntonOsika/gpt-engineer/blob/main/ROADMAP.md), and join
[discord](https://discord.gg/8tcDQ89Ej2)
to get input on how you can [contribute](.github/CONTRIBUTING.md) to it.

We are currently looking for more maintainers and community organizers. Email anton.osika@gmail.com if you are interested in an official role.


## Example

https://github.com/AntonOsika/gpt-engineer/assets/4467025/6e362e45-4a94-4b0d-973d-393a31d92d9b
