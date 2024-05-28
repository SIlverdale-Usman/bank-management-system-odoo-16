/** @odoo-module **/

var core = require('web.core');

const { Component, useState,onWillStart } = owl;
import {useService} from "@web/core/utils/hooks";

function generateMarkdown(text) {
    // Headings
    text = text.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    text = text.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    text = text.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold
    text = text.replace(/\*\*(.*)\*\*/gim, '<b>$1</b>');

    // Italic
    text = text.replace(/\*(.*)\*/gim, '<i>$1</i>');

    // Strikethrough
    text = text.replace(/~~(.*)~~/gim, '<s>$1</s>');

    // Blockquote
    text = text.replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>');

    // Ordered List
    text = text.replace(/^\d+\.\s+(.*$)/gim, '<ol><li>$1</li></ol>');
    text = text.replace(/<\/ol>\n<ol>/gim, '\n'); // Fix multiple lists

    // Unordered List
    text = text.replace(/^\*\s+(.*$)/gim, '<ul><li>$1</li></ul>');
    text = text.replace(/^\-\s+(.*$)/gim, '<ul><li>$1</li></ul>');
    text = text.replace(/<\/ul>\n<ul>/gim, '\n'); // Fix multiple lists

    // Inline Code
    text = text.replace(/`(.*?)`/gim, '<code>$1</code>');

    // Paragraphs
    text = text.replace(/\n$/gim, '<br />');

    return text.trim();

}

export default class Assistant extends Component{
    buttonState = true
    setup(){
        this.state = useState({
            query:{question:"",answer:""},
            queryList:[],
        });
        this.orm = useService("orm");
        this.model = "bank.assistant";

        onWillStart(async () => {
            await this.fetchChat()
        });
    }

    async fetchChat() {
        this.state.queryList = await this.orm.searchRead(this.model,[],["question","answer"])
    }

    async askAi(){
        this.buttonState = false

        const question = this.state.query.question;
        const response = await this.orm.call(this.model,"generate_answer",[[]],{
            query: question,
        });

        this.state.query.answer = generateMarkdown(response)
        await this.orm.create(this.model, [this.state.query])
        this.buttonState = true

        await this.fetchChat()

    }
};

Assistant.template = 'bank.assistantTemplate';
core.action_registry.add('bank.assistantAction', Assistant);