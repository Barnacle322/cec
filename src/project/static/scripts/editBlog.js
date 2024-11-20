const blog_id = window.location.href.split("/").slice(-2)[0];
const dataUrl = window.location.href.replace("edit", "data");
const statusUrl = window.location.href.replace("edit", "publish-status");

let db_blog = {};
let localStorageObject = localStorage.getItem(blog_id);
let indicator = document.getElementById("change-indicator");
let discard_button = document.getElementById("discard-button");

let editor = new EditorJS({
    holder: "editorjs",
    placeholder: "Давайте напишем крутую историю!",

    tools: {
        header: {
            class: Header,
            inlineToolbar: true,
            shortcut: "CMD+SHIFT+H",
        },
        list: {
            class: EditorjsList,
            inlineToolbar: true,
        },
        embed: {
            class: Embed,
            inlineToolbar: true,
            config: {
                services: {
                    youtube: true,
                    coub: true,
                },
            },
        },
        image: {
            class: ImageTool,
            config: {
                endpoints: {
                    byFile: "/admin/blog/image/upload",
                    byUrl: "/admin/blog/image/fetch",
                },
            },
        },
        quote: {
            class: Quote,
            inlineToolbar: true,
        },
        linkblock: {
            class: LinkTool,
            config: {
                endpoint: "/admin/blog/link",
            },
        },
        marker: {
            class: Marker,
        },
        delimiter: Delimiter,
    },
    i18n: {
        /**
         * @type {I18nDictionary}
         */
        messages: {
            /**
             * Other below: translation of different UI components of the editor.js core
             */
            ui: {
                blockTunes: {
                    toggler: {
                        "Click to tune": "Нажмите, чтобы настроить",
                        "or drag to move": "или перетащите",
                    },
                },
                inlineToolbar: {
                    converter: {
                        "Convert to": "Конвертировать в",
                    },
                },
                toolbar: {
                    toolbox: {
                        Add: "Добавить",
                    },
                },
            },

            /**
             * Section for translation Tool Names: both block and inline tools
             */
            toolNames: {
                Text: "Параграф",
                Heading: "Заголовок",
                List: "Список",
                "Unordered List": "Маркированный список",
                "Ordered List": "Нумерованный список",
                Checklist: "Чеклист",
                Image: "Изображение",
                Warning: "Примечание",
                Quote: "Цитата",
                Code: "Код",
                Delimiter: "Разделитель",
                "Raw HTML": "HTML-фрагмент",
                Table: "Таблица",
                Link: "Ссылка",
                Marker: "Маркер",
                Bold: "Полужирный",
                Italic: "Курсив",
                InlineCode: "Моноширинный",
            },

            /**
             * Section for passing translations to the external tools classes
             */
            tools: {
                /**
                 * Each subsection is the i18n dictionary that will be passed to the corresponded plugin
                 * The name of a plugin should be equal the name you specify in the 'tool' section for that plugin
                 */
                warning: {
                    // <-- 'Warning' tool will accept this dictionary section
                    Title: "Название",
                    Message: "Сообщение",
                },

                /**
                 * Link is the internal Inline Tool
                 */
                link: {
                    "Add a link": "Вставьте ссылку",
                },
                /**
                 * The "stub" is an internal block tool, used to fit blocks that does not have the corresponded plugin
                 */
                stub: {
                    "The block can not be displayed correctly.": "Блок не может быть отображен",
                },
            },

            /**
             * Section allows to translate Block Tunes
             */
            blockTunes: {
                /**
                 * Each subsection is the i18n dictionary that will be passed to the corresponded Block Tune plugin
                 * The name of a plugin should be equal the name you specify in the 'tunes' section for that plugin
                 *
                 * Also, there are few internal block tunes: "delete", "moveUp" and "moveDown"
                 */
                delete: {
                    Delete: "Удалить",
                },
                moveUp: {
                    "Move up": "Переместить вверх",
                },
                moveDown: {
                    "Move down": "Переместить вниз",
                },
            },
        },
    },
    onChange: (api, event) => {
        editor
            .save()
            .then((outputData) => {
                const dataString = JSON.stringify({
                    data: outputData,
                    title: document.getElementById("title").value,
                });
                localStorage.setItem(blog_id, dataString);
                if (db_blog) {
                    if (JSON.stringify(db_blog.blocks) == JSON.stringify(outputData.blocks)) {
                        indicator.innerText = "Сохранено";
                        indicator.style.fontStyle = "";
                        indicator.classList.remove("text-black");
                        indicator.classList.add("text-gray-300");
                    } else {
                        indicator.innerText = "Есть изменения";
                        indicator.style.fontStyle = "italic";
                        indicator.classList.add("text-black");
                        indicator.classList.remove("text-gray-300");

                        discard_button.disabled = false;
                    }
                }
            })
            .catch((error) => {
                console.log(error);
            });
    },
});

window.addEventListener("DOMContentLoaded", async () => {
    db_blog = await fetch(dataUrl).then((data) => data.json());

    localStorageObject = localStorageObject
        ? JSON.parse(localStorageObject)
        : { title: document.getElementById("title").value, data: {} };
    if (db_blog) {
        if (
            JSON.stringify(db_blog.blocks) === JSON.stringify(localStorageObject.data.blocks) ||
            localStorageObject.data.blocks == null
        ) {
            indicator.innerText = "Сохранено";
            indicator.style.fontStyle = "";
            indicator.classList.remove("text-black");
            indicator.classList.add("text-gray-300");

            discard_button.disabled = true;
        } else {
            indicator.innerText = "Есть изменения";
            indicator.style.fontStyle = "italic";
            indicator.classList.add("text-black");
            indicator.classList.remove("text-gray-300");

            discard_button.disabled = false;
        }
    }

    editor.isReady
        .then(() => {
            if (localStorageObject.data.blocks) {
                editor.render(localStorageObject.data);
            } else if (db_blog) {
                editor.render(db_blog);
            } else {
                editor.render({ blocks: [] });
            }
        })
        .catch((error) => {
            console.log(error);
        });
});

async function discardChanges() {
    localStorage.removeItem(blog_id);

    db_blog = await fetch(dataUrl).then((data) => data.json());
    if (db_blog) {
        editor.render(db_blog);
    } else {
        editor.render({ blocks: [] });
    }

    discard_button.disabled = true;

    indicator.innerText = "Сохранено";
    indicator.style.fontStyle = "";
    indicator.classList.add("text-gray-300");
    indicator.classList.remove("text-black");
}

async function saveArticle() {
    const outputData = await editor.save().then((data) => data);
    const dataString = JSON.stringify({
        data: outputData,
        title: document.getElementById("title").value,
    });
    let response = await fetch("", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: dataString,
    }).then((data) => data);

    localStorage.removeItem(blog_id);

    db_blog = await fetch(dataUrl).then((data) => data.json());
    editor.render(db_blog);

    discard_button.disabled = true;

    indicator.innerText = "Сохранено";
    indicator.style.fontStyle = "";
    indicator.classList.add("text-gray-300");
    indicator.classList.remove("text-black");
}

function changeStatus(status) {
    const statusData = JSON.stringify({ is_draft: status });
    let response = fetch(statusUrl, {
        method: "POST",
        body: statusData,
    }).then((data) => {
        data;
        location.reload();
    });
}
