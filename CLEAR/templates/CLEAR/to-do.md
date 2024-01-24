materials.html
1. figure out a way to display the to-be created material's ID. current implementation does not display proper value when the latest material is deleted

products.html
1. finalize return redirect (should apply to other forms if problems arise)
2. figure out a way to dynamically update unit field as a material is selected

3. finish up dynamic adding and deleting of rows. (just need to implement the event handler delete and adjust addrow func)

orders.html

3. revist order and item relations. Should an item really be stored once the orders its on is deleted? why do we need an order_item? item should be directly stored on an order, together with quantity
4. where da heck is the delete button on edit order
5. revisit customer entity. why do we have a customer entity if we can't delete it or edit it? would it not be better to have the customer be a field on the order entity instead?


global
1. add comments to organize code
2. consider implementing django's form classes and choices for relevant fields
3. error messages
4. figure out a way to dynamically update ID fields to show a to-be created entity's or a chosen entity's id 
5. edits are not discarded upon closing a modal
6. implement scrolling elements to the table and material/items
7. implement add button to all the add and edit forms where rows need to be added on click of a button


