import streamlit as st
import pandas as pd
from st_supabase_connection import SupabaseConnection, execute_query
from anthropic import Anthropic

st.set_page_config(layout="wide")

# Initialize Supabase connection
st_supabase_client = st.connection(
    name="test",
    type=SupabaseConnection,
    url=st.secrets["SUPABASE_URL"],
    key=st.secrets["SUPABASE_KEY"],
    ttl=None,
)

if "selected_patterns" not in st.session_state:
    st.session_state.selected_patterns = ""
if "isChecked" not in st.session_state:
    st.session_state.isChecked = False

# At the beginning of your script, add this initialization
if "selected_checkbox" not in st.session_state:
    st.session_state.selected_checkbox = None

if "claude" not in st.session_state:
    st.session_state.claude = Anthropic(api_key=st.secrets["ClaudeAPIKey"])


# Define a callback function
def checkbox_changed(checkbox_key, patterns):
    if st.session_state[checkbox_key]:
        st.session_state.selected_checkbox = checkbox_key
        st.session_state.selected_patterns = patterns
        st.session_state.isChecked = True
    elif st.session_state.selected_checkbox == checkbox_key:
        st.session_state.selected_checkbox = None
        st.session_state.selected_patterns = ""
        st.session_state.isChecked = False


def get_ai_response(prompt):
    # Placeholder for AI response
    return f"AI response to: {prompt}"


def fetch_patterns():
    # Fetch patterns from Supabase
    result = execute_query(st_supabase_client.table("Patterns").select("*"), ttl=0)
    return pd.DataFrame(result.data)


def call_claude(prompt, client: Anthropic):
    response = client.messages.create(
        model="claude-sonnnet-...",
        max_tokens=1000,
        temperature=0.5,
        system=st.session_state.selected_patterns,
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    return response.content[0].text


def main():
    st.title("Two-Column Layout with Supabase Integration")

    # Create two columns
    col1, col2 = st.columns(2)

    # Column 1: Chat Input
    with col1:
        st.header("Chat Input")
        container = st.container(height=600)

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("What is up?"):
            print(st.session_state.selected_patterns)
            st.session_state.messages.append({"role": "user", "content": prompt})
            container.markdown(f"You: {prompt}")

            response = get_ai_response(prompt)
            container.markdown(f"AI: {response}")
            st.session_state.messages.append({"role": "assistant", "content": response})

    # Column 2: Patterns
    with col2:
        st.header("Patterns")

        # Fetch patterns from Supabase
        df = fetch_patterns()

        # Create a scrollable container for patterns
        patterns_container = st.container(height=600)

        # Display the table with interactive checkboxes inside the scrollable container
        with patterns_container:
            for i, row in df.iterrows():
                col1, col2, col3 = st.columns([1, 4, 6])
                with col1:
                    # Create a unique key for each checkbox
                    checkbox_key = f"checkbox_{i + 1}"

                    # Check if this checkbox should be checked
                    is_checked = st.session_state.selected_checkbox == checkbox_key

                    # Render the checkbox
                    st.checkbox(
                        f"Select {i+1}",
                        key=checkbox_key,
                        value=is_checked,
                        label_visibility="collapsed",
                        on_change=checkbox_changed,
                        args=(checkbox_key, "".join(row["patterns"])),
                    )
                with col2:
                    file_name = (
                        row["file_name"] if "file_name" in row else f"Pattern {i+1}"
                    )
                    st.write(file_name.capitalize())
                with col3:
                    # Display the preview of the pattern
                    patterns = (
                        row["patterns"] if "patterns" in row else f"Preview {i+1}"
                    )
                    pattern_string = "".join(patterns)
                    pattern_string = (
                        pattern_string.replace("#", " ")
                        .replace("\n", " ")
                        .replace("IDENTITY and PURPOSE", "")
                        .replace("-", " ")
                    )
                    st.write(
                        pattern_string[:80] + "..."
                        if len(pattern_string) > 100
                        else pattern_string
                    )


if __name__ == "__main__":
    main()
    st.write(st.session_state.selected_patterns)
