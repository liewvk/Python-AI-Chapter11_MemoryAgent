# main.py
import sys
from ollama import ResponseError
from memory_store import MemoryStore, ShortTermChat
from ollama_service import OllamaService
from settings import MODEL_NAME, MEMORY_FILE, MAX_QUESTION_LENGTH


def help_text():
    print("\nCommands:")
    print("  /remember category | information  Save a memory")
    print("  /memories                         List saved memories")
    print("  /recall keywords                  Search saved memories")
    print("  /update ID | revised information  Edit a memory")
    print("  /forget ID                        Delete a memory")
    print("  /history                          Show recent chat")
    print("  /clear                            Clear recent chat only")
    print("  /status                           Show memory counts")
    print("  /help                             Show commands")
    print("  /exit                             Close program")
    print("Categories: project, preference, goal, note")


def display_memories(items):
    if not items:
        print("No matching memories.")
        return
    for item in items:
        print(f"[{item['id']}] {item['category']}: {item['text']}")


def command(line, store, chat):
    action, _, args = line.partition(" ")
    action = action.lower()
    args = args.strip()
    if action == "/help":
        help_text()
    elif action == "/remember":
        category, sep, text = args.partition("|")
        if not sep:
            raise ValueError("Use /remember category | information")
        text = text.strip()
        print("Save this information locally?", text)
        if input("Type YES to confirm: ").strip() == "YES":
            item = store.add(category, text)
            print("Saved with ID:", item["id"])
        else:
            print("Canceled.")
    elif action == "/memories":
        display_memories(store.list_all())
    elif action == "/recall":
        if not args:
            raise ValueError("Use /recall keywords")
        display_memories(store.search(args))
    elif action == "/update":
        identifier, sep, text = args.partition("|")
        if not sep:
            raise ValueError("Use /update ID | revised information")
        updated = store.update(identifier.strip(), text)
        print("Updated:", updated["id"])
    elif action == "/forget":
        if not args:
            raise ValueError("Use /forget ID")
        if input(f"Delete memory {args}? Type YES: ").strip() == "YES":
            store.forget(args)
            print("Memory deleted from the local store.")
        else:
            print("Canceled.")
    elif action == "/history":
        if not chat.messages:
            print("No recent chat messages.")
        else:
            for message in chat.messages:
                print(f"{message['role'].title()}: {message['content']}")
    elif action == "/clear":
        chat.clear()
        print("Recent chat cleared; saved memories unchanged.")
    elif action == "/status":
        print(f"Saved memories: {len(store.items)}")
        print(f"Recent exchanges: {len(chat.messages) // 2}")
        print("Memory file:", MEMORY_FILE)
    else:
        print("Unknown command. Type /help.")


def main():
    print("PYTHON AI AGENT WITH MEMORY")
    print("Visual Studio 2026 | Ollama |", MODEL_NAME)
    print("Interpreter:", sys.executable)
    try:
        store = MemoryStore()
    except (OSError, ValueError) as exc:
        print("Could not load saved memory:", exc)
        print("Inspect the memory file before continuing.")
        return
    chat = ShortTermChat()
    service = OllamaService()
    help_text()
    while True:
        try:
            line = input("\nYou: ").strip()
            if not line:
                continue
            if line.lower() == "/exit":
                print("Goodbye!")
                break
            if line.startswith("/"):
                try:
                    command(line, store, chat)
                except (ValueError, OSError) as exc:
                    print("Command failed:", exc)
                continue
            if len(line) > MAX_QUESTION_LENGTH:
                print("Question is too long.")
                continue
            remembered = store.search(line)
            answer = service.ask(line, chat.recent(), remembered)
            print("\nAssistant:", answer)
            chat.add_exchange(line, answer)
            print(f"[Used {len(remembered)} saved memory item(s)]")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        except (ResponseError, ConnectionError, TimeoutError, ValueError) as exc:
            print("AI request failed:", exc)
        except Exception as exc:
            print("Unexpected error:", exc)


if __name__ == "__main__":
    main()
