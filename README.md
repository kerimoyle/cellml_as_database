# Cellml as a database
 
This is my scratch pad for seeing how an online database for CellML (and perhaps SBML?) manipulation could work.  

This idea differs in pradigm from the current libCellML and OpenCOR implementations by saving items (units, variables, maths, etc) separately as distinct-but-linked rows in a relational database rather than text in an XML file.  Each database table is configured to represent a different item type, with fields and relationships as appropriate.  The hope is that:
- users will be able to reuse and assemble models faster than currently, as items can be linked into a model without needing to download, copy, paste or reference the entire workspace of the model they are copied from 
- users will be able to assemble, valdiate, and debug models online before exporting/downloading for simulation.  This means that there is no need to **retranslate** a simulated model (from whatever language it is run in) back into *.cellml format before incluion in the Physiome Model Repository - the model never leaves the database.
- users will be able to save notes, comments, etc against any part of their model.  Comments are not allowed in CellML 2.0 format so this will preserve their contents while enabling models to be written and run in the 2.0 format.


## Use cases

1. Upload existing **unannotated** CellML2.0 model:
    1. Upload and read *.cellml file
    2. Save content as distinct but linked items in own library
        - **NB** Default privacy is private for the highest level of the imported item (probably the model) and inherited by its children.  
        -  **NB** The user is set as the original creator of the model and its constituent items 
        
2. Upload existing **annotated** CellML2.0 model (ie: *.cellml and *.rdf files together)
    1. Upload and read *.cellml file
    2. Upload and read *.rdf file
    2. Save content as distinct but linked items in user's own library, where the annotations are stored as links to the appropriate items
        - **NB** Default privacy is private for the highest level of the imported item (probably the model) and inherited by its children.  
        -  **NB** The user is set as the original creator of the model unless the annotations indicate provenance.  The provenance will not be a link to an item in the database but will preserve the appropriate referencing text, if found.  **NB** need to check if this is standardised beyond just the semsim:hasCellMLdocumentation block?
        
3. Upload existing CellML1.0/1.1 model:
    1. Upload and read file
    2. Save content as distinct but linked items in own library where possible, return parse warnings where items are cannot be stored because of their version/format (old resets, old unit spellings, offsets, etc)
    3. Save comment blocks into the notes field of relevant items

2. Create new item (model/component/units/variable etc) from scratch
    1. Fill in form of required fields
    2. Save item to own library
        - Note that creation from scratch using the form will set the user to be the original owner of the item, the root of the provenance tree.
        
3. Create annotations for item   
    1. Search annotation ontologies for appropriate languages and codes and select
        - **NB** Suggestions from learned behaviours/smart searches/interpreted uses could be used here
    2. Enter freeform comments and text as required
    3. Save annotation for item

3. Locate items for inclusion in model
    1. Informed search based on annotations, previous usage, recommender system (from Dewan)
    2. Indexes all public items in database, could also include PMR/Weblab contents?

3. Import existing item from public library
    1. If the item is to be used 'as-is' then it can be imported as a **link** to the public original.  The rationale of this setup is that items are distinct-but-linked: models are formed by the relationships between items, and whether those items are concrete and "owned" by the user or linked from elsewhere has no impact on their use.
        - Note that linked items are susceptible to changes in the item to which they link: if the owner of the item changes it then the user's linked copy will also be changed.
    2. If the item is to be edited by the user, it can be **duplicated** into the user's library.  This allows the user to be safe from upstream changes (as above) and also to edit any part of the item.  
        - They now "own" their own concrete instance of the item, but the provenance (the fact that it was copied from someone else's item) remains.
    - **NB** The item to be imported could be an annotation instance as well as a model item, though annotation instances would be imported as concrete (cf links).
    
4. Understand model syntactic validity 
    1. During the process of creating the model the user can see a "todo" list of actions needed before the model is valid.  The import/creation/editing/export of an *invalid* model is permitted, but the user will see where and how it needs fixing.
    - **NB** This checks _only_ the requirements of the validator against the model.  It does not check whether the operation of the model is reasonable or sensible.
    2. Users will see a list of non-critical warnings, such as mismatched prefix/multipliers between units of equivalent variables, deprecation of American spellings, etc.
    
5. Prepare/debug/tune model
    1. Before exporting the user can debug the model by:
        1. plotting the behaviour of mathml blocks
        2. rendering the mathml blocks to display format
        2. tracing dependency relationships of variables and units in a visual way
        3. ... etc ...?
    2. The user can upload data to the math blocks to estimate parameter values and see how they fit the data
    3. Link to the Weblab for comparison or searching for similar items and their parameters?
    2. Non-critical warnings/hints from the valdiator shown
    
6. Export the model for simulation
    1. Export the model into the language of choice (using the new code generation part of libcellml) for simulation.  
    - **NB** the model, its annotations and notes **remain** in the database, they do not need to be reuploaded later on.
    2. Generate a persistent URL to the model location for reference from other places



    
    
  

