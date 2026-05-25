#!/usr/bin/env python3
"""
Setup Verification Script
=========================
Validates that all dependencies are installed and all three API keys work
BEFORE running the pilot experiment (which costs API money).

Run this first:
    python setup_check.py

Expected output: 6 green checkmarks. If any fail, fix that issue first.
"""

import asyncio
import os
import sys


def header(s):
    print(f"\n{'─' * 60}\n  {s}\n{'─' * 60}")


def ok(s):
    print(f"  \033[32m✓\033[0m {s}")


def fail(s):
    print(f"  \033[31m✗\033[0m {s}")


def check_packages():
    header("1. Package availability")
    required = ["anthropic", "openai", "google.genai", "aiosqlite"]
    all_ok = True
    for pkg in required:
        try:
            __import__(pkg if pkg != "google.genai" else "google.genai")
            ok(f"{pkg} importable")
        except ImportError as e:
            fail(f"{pkg} NOT importable: {e}")
            all_ok = False
    return all_ok


def check_env_vars():
    header("2. Environment variables")
    keys = {
        "ANTHROPIC_API_KEY": "sk-ant-",
        "OPENAI_API_KEY":    "sk-",
        "GOOGLE_API_KEY":    "AIza",
    }
    all_ok = True
    for var, prefix in keys.items():
        val = os.environ.get(var)
        if not val:
            fail(f"{var} is not set")
            all_ok = False
        elif not val.startswith(prefix):
            fail(f"{var} set but does not start with '{prefix}'  Echeck key")
            all_ok = False
        else:
            masked = f"{val[:8]}...{val[-4:]}"
            ok(f"{var} set ({masked})")
    return all_ok


async def check_claude():
    header("3. Anthropic API live call")
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=20,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        )
        text = resp.content[0].text.strip()
        ok(f"Claude responded: {text!r}")
        return True
    except Exception as e:
        fail(f"Claude call failed: {e}")
        return False


async def check_openai():
    header("4. OpenAI API live call")
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resp = await client.chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=20,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        )
        text = resp.choices[0].message.content.strip()
        ok(f"GPT-4.1 mini responded: {text!r}")
        return True
    except Exception as e:
        fail(f"OpenAI call failed: {e}")
        return False


async def check_gemini():
    header("5. Google Gemini API live call")
    try:
        from google import genai
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        resp = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=[{"role": "user", "parts": [{"text": "Reply with exactly: OK"}]}],
            config=genai.types.GenerateContentConfig(max_output_tokens=20),
        )
        text = resp.text.strip()
        ok(f"Gemini 2.5 Flash responded: {text!r}")
        return True
    except Exception as e:
        fail(f"Gemini call failed: {e}")
        return False


async def check_judge():
    header("6. Judge model (GPT-4.1 full) live call")
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resp = await client.chat.completions.create(
            model="gpt-4.1",
            max_tokens=20,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
        )
        text = resp.choices[0].message.content.strip()
        ok(f"GPT-4.1 responded: {text!r}")
        return True
    except Exception as e:
        fail(f"GPT-4.1 call failed: {e}")
        return False


async def main():
    print("\n" + "=" * 60)
    print("  SETUP VERIFICATION")
    print("=" * 60)

    pkg_ok = check_packages()
    if not pkg_ok:
        print("\n  Fix packages first: pip install anthropic openai "
              "google-genai aiosqlite")
        sys.exit(1)

    env_ok = check_env_vars()
    if not env_ok:
        print("\n  Set missing environment variables and re-run.")
        sys.exit(1)

    results = await asyncio.gather(
        check_claude(),
        check_openai(),
        check_gemini(),
        check_judge(),
    )

    print("\n" + "=" * 60)
    if all(results):
        print("  \033[32mALL CHECKS PASSED.\033[0m Run: python pilot.py")
    else:
        print("  \033[31mSOME CHECKS FAILED.\033[0m Fix issues above and re-run.")
    print("=" * 60 + "\n")

    sys.exit(0 if all(results) else 1)


if __name__ == "__main__":
    asyncio.run(main())
