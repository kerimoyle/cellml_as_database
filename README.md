# cellml_as_database
 
This is my scratch pad for seeing how an online database for CellML (and perhaps SBML?) manipulation could work.  

This idea differs in pradigm from the current libCellML and OpenCOR implementations by saving items (units, variables, maths, etc) separately as distinct rows in a relational database.  Each database table is configured to represent a different item type, with fields and relationships as appropriate.  The hope is that:
- users will be able to reuse and assemble models faster than currently, as items can be linked into a model without needing to download, copy, paste or reference the entire workspace of the model they are copied from 
- users will be able to assemble, valdiate, and debug models online before exporting/downloading for simulation.  This means that there is no need to **retranslate** a simulated model (from whatever language it is run in) back into *.cellml format before incluion in the Physiome Model Repository - the model never leaves the database.







## Use cases

1. Upload existing CellML2.0 model:
    1. Upload and read *.cellml file
    2. Save content as distinct but linked items in own library
        - Default privacy is private for the highest level of the imported item (probably the model) and inherited by its children.  
        - The user is set as the original creator of the model and its constituent items
        
2. Create new item (model/component/units/variable etc) from scratch
    1. Fill in form of required fields
    2. Save item to own library
        - Note that creation from scratch using the form will set the user to be the original owner of the item, the root of the provenance tree.
    
3. Import existing item from public library
    1. If the item is to be used 'as-is' then it can be imported as a **link** to the public original.  The rationale of this setup is that items are distinct-but-linked: models are formed by the relationships between items, and whether those items are concrete and "owned" by the user or linked from elsewhere has no impact on their use.
        - Note that linked items are susceptible to changes in the item to which they link: if the owner of the item changes it then the user's linked copy will also be changed.
    2. If the item is to be edited by the user, it can be **duplicated** into the user's library.  This allows the user to be safe from upstream changes (as above) and also to edit any part of the item.  They now "own" their own concrete instance of the item, but the provenance (the fact that it was copied from someone else's item) remains.
    
  

