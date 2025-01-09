def run_manager():
    # 1. Connect to firebase
    # 2. load index in to terms
    # 3. fill dropbox with options (all the words which are the keys in the index)
    # 4. let the user select a word and edit or remove links and counts.
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
        terms = FBconn.get('/Index/', None)
        display(HTML(f"<p style='color: green;'>Index restored successfuly!</p>"))
        refresh_html(dropdown.value)
      #except Exception as e:
      # display(HTML(f"<p style='color: red;'>Failed to restore index: {e}.</p>"))

    # Function to refresh the table's HTML content
    def refresh_html(selected_word):
        clear_output(wait=True)
        
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
            else:
                print(f"'docs' is not a dictionary. Got: {type(links)}")
        else:
            print(f"Unexpected data type for '{selected_word}': {type(data)}")

    # Function to remove link from a term's doc list
    def remove_link(term, link):
        try:
            terms[term] = json.loads(terms[term])
            del terms[term]['DocIDs'][link]  # Remove the link locally
            terms[term] = json.dumps(terms[term])
            refresh_html(term)  # Refresh the HTML content
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
      refresh_html(selected_term)

    # Function to save the updated index back to Firebase
    def save_to_firebase():
        try:
            FBconn.put('/', '/Index/', terms)  # Upload the updated `terms` dictionary
            message = "<div id='message' style='color: green; font-weight: bold;'>Successfully saved to Firebase!</div>"
        except Exception as e:
            message = f"<div id='message' style='color: red; font-weight: bold;'>Error: {e}</div>"
        display(HTML(message))
        refresh_html(dropdown.value)

    # Function to handle word selection
    def on_word_select(change):
        global selected_term
        selected_word = change['new']
        selcted_term = change['new']
        refresh_html(selected_word)

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
            # If term exists, update its DocIDs
            if new_term in terms:
                term_data = json.loads(terms[new_term])
                term_data['DocIDs'][new_link] = new_count
                terms[new_term] = json.dumps(term_data)
               
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
                
            # Update dropdown options
            dropdown.options = list(terms.keys())
             # also update the firebase index. index index will have new url and count
            FBconn.put('/Index/', new_term, terms[new_term])
            
            # Clear form
            new_term_text.value = ""
            new_link_text.value = ""
            new_count_text.value = 1
            
            # Refresh display
            refresh_html(dropdown.value)
            display(HTML("<p style='color: green;'>Term added successfully!</p>"))
            
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
    refresh_html(dropdown.value)
    selected_term=dropdown.value