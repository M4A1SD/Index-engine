import ipywidgets as widgets
from IPython.display import display, HTML
import json
import firebase_admin
from firebase import firebase

css = """
<style>
.modern-table {
    width: 100%;
    border-collapse: collapse;
    margin: 25px 0;
    font-size: 0.9em;
    font-family: sans-serif;
    min-width: 400px;
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
}
.modern-table thead tr {
    background-color: #009879;
    color: #ffffff;
    text-align: left;
}
.modern-table th,
.modern-table td {
    padding: 12px 15px;
}
.modern-table tbody tr {
    border-bottom: 1px solid #dddddd;
}
.remove-button {
    background-color: #dc3545;
    color: white;
    border: none;
    padding: 5px 10px;
    border-radius: 3px;
    cursor: pointer;
    margin-right: 5px;
}
.edit-button {
    background-color: #ffc107;
    color: black;
    border: none;
    padding: 5px 10px;
    border-radius: 3px;
    cursor: pointer;
}
</style>
"""

js = """
<script>
document.getElementById('save-button').onclick = function() {
    google.colab.kernel.invokeFunction('notebook.save_to_firebase', [], {});
};

// Function to update content within the manager container
function updateTermContent(content) {
    const container = document.getElementById('manager-container');
    const existingContent = document.getElementById('term-content');
    if (existingContent) {
        existingContent.outerHTML = content;
    } else {
        container.insertAdjacentHTML('beforeend', content);
    }
}
</script>
"""

def run_manager():
    # Create a container div for all manager content
    display(HTML("""
    <div id="manager-container">
        <style>
        #manager-container {
            padding: 20px;
        }
        """ + css.replace('<style>', '').replace('</style>', '') + """
        </style>
    </div>
    """))

    # Update the JavaScript to insert content into the container
    global js
    js = """
    <script>
    document.getElementById('save-button').onclick = function() {
        google.colab.kernel.invokeFunction('notebook.save_to_firebase', [], {});
    };

    // Function to update content within the manager container
    function updateTermContent(content) {
        const container = document.getElementById('manager-container');
        const existingContent = document.getElementById('term-content');
        if (existingContent) {
            existingContent.outerHTML = content;
        } else {
            container.insertAdjacentHTML('beforeend', content);
        }
    }
    </script>
    """

    # Firebase connection
    FBconn = firebase.FirebaseApplication("https://wolf-db-bfac4-default-rtdb.europe-west1.firebasedatabase.app/", None)
    global terms
    terms = FBconn.get('/Index/', None)

    # Front End Compontents:
    # Dropdown widget for selecting words
    dropdown = widgets.Dropdown(
        options=terms.keys(),
        description="Words:",
        disabled=False
    )
    # Textfield for editing link
    link_text = widgets.Text(
        value="",
        placeholder="https://example.com/",
        description = "DocID: ",
        disabled=True
    )
    # Label for term
    term_label = widgets.Label(
        value = "Term",
        disabled = True
    )
    # Textfield for editing count
    count_text = widgets.IntText(
        value = 13,
        description = "Count: ",
        disabled=True
    )
    # Button to save editing changes
    save_edit_btn = widgets.Button(
        description = "Save Edit",
        disabled = True,
        button_style = 'info',
        icon = 'check'
    )
    global selected_link
    global selected_count
    global selected_term
    # This function completely restores the index, scraping MS Azure again.
    def restore_index():
      #try:
        db = DatabaseService()
        db.restore_index()
        db.upload_index()
        global terms
        terms = FBconn.get('/Index/', None)
        # Update dropdown options with new terms
        dropdown.options = list(terms.keys())
        display(HTML(f"<p style='color: green;'>Index restored successfully!</p>"))
        # Refresh display if there's a selected value
        if dropdown.value:
            display_links_for_term(dropdown.value)
        # i need a solution to show new changes(dropdown.value)
      #except Exception as e:
      # display(HTML(f"<p style='color: red;'>Failed to restore index: {e}.</p>"))


        
        # Display add term form
        display(HTML("<h3>Add a term to index</h3>"))
        display(new_term_text)
        display(new_link_text)
        display(new_count_text)
        display(add_term_btn)
        
        display(HTML("<h3>Edit existing terms</h3>"))
        display(dropdown)
        
        data = terms[selected_word]
        data = json.loads(data)

        if isinstance(data, dict):
            links = data.get('DocIDs', {})
            if isinstance(links, dict):
                html_content = css
                html_content += "<table class='modern-table'>"
                html_content += "<thead><tr><th>Link</th><th>Count</th><th>Actions</th></tr></thead>"
                html_content += "<tbody>"
                for link, count in links.items():
                    html_content += f"<tr>"
                    html_content += f"<td><a href='{link}' target='_blank' style='text-decoration: none; color: #007BFF;'>{link}</a></td>"
                    html_content += f"<td>{count}</td>"
                    html_content += f"<td>"
                    html_content += f"<button onclick='google.colab.kernel.invokeFunction(\"notebook.remove_link\", [\"{selected_word}\", \"{link}\"], {{}})' class='remove-button'>Remove</button>"
                    html_content += f"<button padding: 2px; onclick='google.colab.kernel.invokeFunction(\"notebook.edit_link\", [\"{selected_word}\", \"{link}\",\"{count}\"], {{}})' class='edit-button'>Edit</button>"
                    html_content += f"</td>"
                    html_content += f"</tr>"
                html_content += "</tbody></table>"

                # Add Save button
                html_content += "<br><button id='save-button' style='background-color: #28A745; color: white; border: none; border-radius: 5px; padding: 10px 20px; cursor: pointer;'>Save Index</button>"
                #html_content += "<br><button id='restore-button' style='margin-top: 10px; background-color: #8B8000; color: white; border: none; border-radius: 5px; padding: 10px 20px; cursor: pointer;'>Restore Index</button>"
                html_content += "<p>Uploads index to database.</p>"
                # JavaScript to trigger Python function
                html_content += js
                term_label.disabled=True
                link_text.disabled=True
                count_text.disabled=True
                save_edit_btn.disabled=True
                display(HTML(html_content))
                display(term_label)
                display(link_text)
                display(count_text)
                display(save_edit_btn)


    # Function to remove link from a term's doc list
    def remove_link(term, link):
        try:
            terms[term] = json.loads(terms[term])
            del terms[term]['DocIDs'][link]  # Remove the link locally
            terms[term] = json.dumps(terms[term])
            # Now refresh the display with updated data
            display_links_for_term(term)
        except Exception as e:
            print(f"Error while removing link: {e}")

    # This function allows editing the link of the selected term
    def edit_link(term,link,count):
      global selected_link
      global selected_count
      selected_link = link
      print(selected_link)
      selected_count = count
      link_text.value = link
      # link_text.disabled = False
      term_label.value=term
      term_label.disabled = False
      count_text.value = count
      count_text.disabled = False
      save_edit_btn.disabled = False
      save_edit_btn.on_click(on_save_edit_btn_click)


    def on_save_edit_btn_click(event):
      global selected_term
      global selected_link
      global terms
      selected_term = dropdown.value
      # delete old tuple, insert new one with text values:
      terms[selected_term]=json.loads(terms[selected_term])
      # If the link remains unchanged, change the count, if the link changed, delete the tuple
      #if selected_link in terms[selected_term]["DocIDs"]:
      print(terms[selected_term]["DocIDs"])
      del terms[selected_term]["DocIDs"][selected_link]
      terms[selected_term]["DocIDs"][link_text.value]=count_text.value
      terms[selected_term]=json.dumps(terms[selected_term])
      
      # Refresh display so updated table is shown:
      display_links_for_term(selected_term)

    # Function to save the updated index back to Firebase
    def save_to_firebase():
        try:
            FBconn.put('/', '/Index/', terms)
            message = "<div id='message' style='color: green; font-weight: bold;'>Successfully saved to Firebase!</div>"
            # Refresh the display after saving
            display_links_for_term(dropdown.value)
        except Exception as e:
            message = f"<div id='message' style='color: red; font-weight: bold;'>Error: {e}</div>"
        display(HTML(message))
        # i need a solution to show new changes(dropdown.value)

    # Function to handle word selection
    def on_word_select(change):
        global selected_term
        selected_word = change['new']
        selected_term = change['new']
        if selected_term:  # Only if something is selected
            display_links_for_term(selected_term)
        # i need a solution to show new changes(selected_word)

    # Add new form components for adding terms
    new_term_text = widgets.Text(
        value="",
        placeholder="Enter new term",
        description="New Term:",
        disabled=False
    )
    
    new_link_text = widgets.Text(
        value="",
        placeholder="https://example.com/",
        description="DocID:",
        disabled=False
    )
    
    new_count_text = widgets.IntText(
        value=1,
        description="Count:",
        disabled=False
    )
    
    add_term_btn = widgets.Button(
        description="Add Term",
        disabled=False,
        button_style='success',
        icon='plus'
    )

    # Function to handle adding a new term
    def on_add_term_btn_click(event):
        new_term = new_term_text.value.strip()
        new_link = new_link_text.value.strip()
        new_count = new_count_text.value
        
        if not all([new_term, new_link, new_count]):
            display(HTML("<p style='color: red;'>All fields are required!</p>"))
            return
            
        try:
            # If term exists, add new link and count
            if new_term in terms:
                term_data = json.loads(terms[new_term])
                term_data['DocIDs'][new_link] = new_count
                terms[new_term] = json.dumps(term_data)
                # update total count
                terms[new_term]["count"]+=new_count
               
            else:
                # Create new term entry
                new_term_data = {
                    "count": new_count,
                    "term": new_term,
                    "DocIDs": {
                        new_link: new_count
                    }
                }
                terms[new_term] = json.dumps(new_term_data)
                # update total count
                
                
            # Update dropdown options
            dropdown.options = list(terms.keys())
             # also update the firebase index. index index will have new url and count
            FBconn.put('/Index/', new_term, terms[new_term])
            
            # Clear form
            new_term_text.value = ""
            new_link_text.value = ""
            new_count_text.value = 1
            
            # Refresh display
            # i need a solution to show new changes(dropdown.value)
            display(HTML("<p style='color: green;'>Term added successfully!</p>"))
            
            # Refresh the display for the newly created / updated term
            display_links_for_term(new_term)
            
        except Exception as e:
            display(HTML(f"<p style='color: red;'>Error adding term: {e}</p>"))

    # Register the add term button callback
    add_term_btn.on_click(on_add_term_btn_click)

    # Register the callbacks with the frontend
    from google.colab import output
    output.register_callback('notebook.save_to_firebase', save_to_firebase)
    output.register_callback('notebook.remove_link', remove_link)
    output.register_callback('notebook.edit_link',edit_link)
    output.register_callback('notebook.restore_index', restore_index)

    # Observe dropdown changes
    dropdown.observe(on_word_select, names='value')

    # Display the dropdown
    # i need a solution to show new changes(dropdown.value)
    selected_term=dropdown.value

    # 1) A new helper function that displays the links & table for a selected term.
    def display_links_for_term(term):
        if not terms:
            display(HTML("<p style='color: red;'>No terms found in the database.</p>"))
            return
        if term not in terms:
            display(HTML(f"<p style='color: red;'>Term '{term}' not found in the database.</p>"))
            return

        data = terms[term]
        data = json.loads(data)

        html_content = """
        <div id="term-content">
            <h3>Edit existing term: {}</h3>
        """.format(term)

        if isinstance(data, dict):
            links = data.get('DocIDs', {})
            if isinstance(links, dict):
                html_content += "<table class='modern-table'>"
                html_content += "<thead><tr><th>Link</th><th>Count</th><th>Actions</th></tr></thead>"
                html_content += "<tbody>"
                for link, count in links.items():
                    html_content += "<tr>"
                    html_content += f"<td><a href='{link}' target='_blank' style='text-decoration: none; color: #007BFF;'>{link}</a></td>"
                    html_content += f"<td>{count}</td>"
                    html_content += "<td>"
                    html_content += f"<button onclick='google.colab.kernel.invokeFunction(\"notebook.remove_link\", [\"{term}\", \"{link}\"], {{}})' class='remove-button'>Remove</button> "
                    html_content += f"<button onclick='google.colab.kernel.invokeFunction(\"notebook.edit_link\", [\"{term}\", \"{link}\",\"{count}\"], {{}})' class='edit-button'>Edit</button>"
                    html_content += "</td>"
                    html_content += "</tr>"
                html_content += "</tbody></table>"

                html_content += "<br><button id='save-button' style='background-color: #28A745; color: white; border: none; border-radius: 5px; padding: 10px 20px; cursor: pointer;'>Save Index</button>"
                html_content += "<p>Uploads index to database.</p>"

        html_content += "</div>"

        # Update JavaScript to include content replacement
        js_with_update = js + """
        <script>
            // Update the content
            updateTermContent(`""" + html_content.replace("`", "\\`") + """`)
        </script>
        """

        # Display the content with update script
        display(HTML(js_with_update))

        # Display widgets once
        if not hasattr(display_links_for_term, 'widgets_displayed'):
            term_label.disabled = True
            link_text.disabled = True
            count_text.disabled = True
            save_edit_btn.disabled = True
            display(term_label)
            display(link_text)
            display(count_text)
            display(save_edit_btn)
            display_links_for_term.widgets_displayed = True

    # Display initial UI elements
    display(HTML("<h3>Add a term to index</h3>"))
    display(new_term_text)
    display(new_link_text)
    display(new_count_text)
    display(add_term_btn)
    
    display(HTML("<h3>Edit existing terms</h3>"))
    display(dropdown)
    
    # Display initial content for the selected term
    if dropdown.value:
        display_links_for_term(dropdown.value)