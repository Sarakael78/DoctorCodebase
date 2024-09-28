import gradio as gr
import os
import logging
from .process import process_codebase, validate_selection

def gradio_process(root_dir, codebase_selection, statistics_selection):
    """
    Handles the Gradio interface processing.
    """
    errors = validate_selection(codebase_selection, statistics_selection)
    if errors:
        return {"error": " ".join(errors)}
    
    output_formats = {
        "Codebase": codebase_selection,
        "Statistics": statistics_selection
    }
    response = process_codebase(root_dir, output_formats)
    return {
        "Status": response.get("status", "Unknown"),
        "Generated Files": response.get("CodeBase", [])
    }

def launch_interface():
    """
    Launches the Gradio interface.
    """
    with gr.Blocks() as iface:
        gr.Markdown("# Codebase Documenter")

        with gr.Row():
            with gr.Column():
                root_dir_input = gr.Textbox(label="Project Root Directory", value=os.getcwd(), lines=1)
            with gr.Column():
                run_button = gr.Button("Run Documenter")
        
        gr.Markdown("## Select Output Formats")

        with gr.Group():
            gr.Markdown("### Codebase Outputs")
            codebase_checkbox = gr.CheckboxGroup(
                choices=["txt", "json", "csv"],
                label="Select formats for Codebase:",
                value=["txt"]
            )

            gr.Markdown("### Statistics Outputs")
            statistics_checkbox = gr.CheckboxGroup(
                choices=["txt", "json", "csv"],
                label="Select formats for Statistics:",
                value=["json"]
            )
        
        output = gr.JSON(label="Output")

        run_button.click(
            fn=gradio_process,
            inputs=[root_dir_input, codebase_checkbox, statistics_checkbox],
            outputs=output
        )

        gr.Markdown("""
        ## Instructions

        1. **Project Root Directory:** Enter the path to your project's root directory. If left blank, the current directory will be used.
        2. **Select Output Formats:**
           - **Codebase Outputs:** Choose among TXT, JSON, and CSV to generate documentation of your codebase.
           - **Statistics Outputs:** Choose among TXT, JSON, and CSV to generate statistics about your codebase.
        3. **Run Documenter:** Click the "Run Documenter" button to generate the selected outputs.
        4. **View Outputs:** The generated files will be saved in the `cd-output` directory within your project root.
        """)

    iface.launch(debug=True)
