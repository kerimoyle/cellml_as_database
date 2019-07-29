# Cellml as a database
 
This is my scratch pad for seeing how an online database for CellML (and perhaps SBML?) manipulation could work.  

This idea differs in paradigm from the current libCellML and OpenCOR implementations by saving items (units, variables, maths, etc) separately as distinct-but-linked rows in a relational database rather than text in an XML file.  Each database table is configured to represent a different item type, with fields and relationships as appropriate.  The hope is that:
- users will be able to reuse and assemble models faster than currently, as items can be linked into a model without needing to download, copy, paste or reference the entire workspace of the model they are copied from 
- users will be able to assemble, valdiate, and debug models online before exporting/downloading for simulation.  This means that there is no need to **retranslate** a simulated model (from whatever language it is run in) back into *.cellml format before incluion in the Physiome Model Repository - the model never leaves the database.
- users will be able to save notes, comments, etc against any part of their model.  Comments are not allowed in CellML 2.0 format so this will preserve their contents while enabling models to be written and run in the 2.0 format.


## Use cases

Glossary:
-	Item: The database contains a table for each kind of CellML object (eg: variable, units, etc).  Because this software is built around reusing templates, they’re all referred to as “items” in this list: that is, creating an item of any flavour reuses the same code.
-	Compound Unit: Referred to in the CellML specifications as “Units” these are a collection of child unit items through a multiplier, exponent, and prefix.  I changed their name for clarity as the plural of an item type name has meaning in the code.
-	Owner: This is not the same as provenance, it refers only to the ability of the user to edit or delete an item.
-	Privacy/visibility: Whether or not an item is visible to users other than its owner is decided by its privacy settings.  Currently these are only public (ie: all users) and private (ie: the owner only) but it would be good to be able to share items with selected users.
-	Public library:  All items in the database which have a “public” visibility status
-	Frozen/archived:  When an item or model is published and stable it can be frozen.  This passes the ownership to a curator instead of the original creator and the item is no longer editable.

1.	**Create**
    1.	Create a concrete item from scratch using the form interface
        1.	Compound unit
        2.	Base unit
        3.	Variable
        4.	Component
        5.	Reset
        6.	Encapsulation
        7.	MathML block
        8.	Model
    2.	Create a concrete item from scratch using XML interface
        1.	(as above)
    3.	Upload CellML2.0 file and save into items
    4.	Upload CellML1.0/1.1 file and save into items
    5.	Upload annotations *.rdf file and save against model

    6.	NB: For all items which are “created” from scratch as above, the user who created them will be listed as the root of the provenance tree.  If there are data in the annotation field which say otherwise (the 


2.	**Discover**
    1.	Search public library:
        1.	Search notes, annotations, names, other usages etc
    2.	Browse public library
    3.	Browse other repositories – weblab? PMR? Etc etc?
    4.	Use recommender system
    5.	Search ontology libraries by annotations and annotated items

3.	**Import to owner’s library**
    1.	Import public item as link (pointer)
    2.	Import public item as local copy (duplicate instance)

4.	**Edit**
    1.	Edit owned item
        1.	Edit local attributes (name, notes, symbol, etc)
        2.	Edit links to child items
        3.	Edit links to parent items
    2.	Change privacy settings on owned item
        1.	Private is visible only to owner
        2.	Public is visible to everyone
    3.	Plot mathml block against nominal variable(s) for debugging
    4.	Upload data to mathml block and plot for parameter tuning
    5.	Render mathml block as equation for debugging
    6.	Freeze/publish item to archive
        1.	Ownership passed to a curator/superuser
        2.	Editing is frozen
        3.	Item will stay public at permanent URL
    7. Allow roll-back changes on items

5.	**Propagate changes**
    1.	When an item to which I have links is deleted
        1.	Create a local copy of the item in my library, maintaining provenance
        2.	Alert the owner of the original item that I have a copy
    2.	When a public item to which I have links is made private:
        1.	Create a local copy of the item in my library, maintaining provenance
        2.	Alert the owner of the original item that I have a copy
    3.	When an item to which I have links is changed
        1.	Alert me that it’s changed
        2.	Alert the owner of the item that it has external links
    4.	When a public item which I own is linked to by another user:
        1.	Alert me
        2.	Propagate provenance chain to the other user’s item


6.	**Validate**
    1.	Validate items in a model 
        1.	Homepage to show to-do list of items and attributes which need addressing before the model is valid
    2.	Visualise dependencies of items 
        1.	Highlight circular units
        2.	Highlight circular variable definitions
        3.	Highlight circular links between items
    3.	Retrieve non-fatal warnings and hints about model composition
        1.	Mis-matched factors in units in variable equivalences
        2.	Mis-matched units in mathml statements
        3.	Deprecated American spellings (liter, meter, deka)
        4.	Deprecated built-in units (Celsius)
        5.	Any conversion from CellML1.0/1.1 to 2.0 for database storage at the time of upload
        6.	… etc … 


7.	**Export**
    1.	Export model to file in selected format using the code generation part of libcellml
        1. Export the model to a *.cellml file
        2. Export the model to a Python file
        3. Export the model to a Matlab file
    2.	Send to a run platform (gigantum or similar?) for online model simulation
    3.	Create permanent URL for model identification and referencing(?)

  

