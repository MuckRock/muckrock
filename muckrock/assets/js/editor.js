import { ProseMirror } from 'prosemirror';
import "prosemirror/dist/inputrules/autoinput";
import 'prosemirror/dist/markdown';
import 'prosemirror/dist/menu/tooltipMenu';

let editor = document.querySelector('textarea.prose-editor');
if (editor) {
    let pm = window.pm = new ProseMirror({
        place: function(newNode){
            editor.parentNode.insertBefore(newNode, editor.nextSibling);
            editor.style.display = 'none';
        },
        doc: editor.value,
        autoInput: true,
        docFormat: 'markdown',
        tooltipMenu: true
    });
    pm.on('change', function(){
        editor.value = pm.getContent("markdown");
    });
}
