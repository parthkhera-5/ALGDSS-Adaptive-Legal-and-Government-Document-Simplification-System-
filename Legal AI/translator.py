# from deep_translator import GoogleTranslator


# class Translator:

#     def __init__(self):

#         print("Loading translator: deep-translator")

#         self.hindi_to_english = GoogleTranslator(
#             source="hi",
#             target="en"
#         )

#         self.english_to_hindi = GoogleTranslator(
#             source="en",
#             target="hi"
#         )

#         print("Translator ready.")

#     # ========================================================
#     # HINDI → ENGLISH
#     # ========================================================

#     def translate_to_english(self, text):

#         if not text or not text.strip():
#             return text

#         try:

#             result = self.hindi_to_english.translate(
#                 text.strip()
#             )

#             return result.strip() if result else text

#         except Exception as e:

#             print(
#                 f"Translation error (HI → EN): {e}"
#             )

#             return text

#     # ========================================================
#     # ENGLISH → HINDI
#     # ========================================================

#     def translate_to_hindi(self, text):

#         if not text or not text.strip():
#             return text

#         text = text.strip()

#         try:

#             result = self.english_to_hindi.translate(text)

#             if result and result.strip():
#                 return result.strip()

#         except Exception as e:

#             print(
#                 f"Translation error (EN → HI): {e}"
#             )

#         # --------------------------------------------------------
#         # Fallback: translate sentence in smaller pieces
#         # --------------------------------------------------------

#         try:

#             sentences = [
#                 s.strip()
#                 for s in text.replace("!", ".").replace("?", ".").split(".")
#                 if s.strip()
#             ]

#             translated_parts = []

#             for sentence in sentences:

#                 try:

#                     result = self.english_to_hindi.translate(
#                         sentence
#                     )

#                     if result and result.strip():
#                         translated_parts.append(
#                             result.strip()
#                         )
#                     else:
#                         translated_parts.append(sentence)

#                 except Exception as e:

#                     print(
#                         f"Sentence translation error: {e}"
#                     )

#                     translated_parts.append(sentence)

#             if translated_parts:
#                 return " ".join(translated_parts)

#         except Exception as e:

#             print(
#                 f"Fallback translation error: {e}"
#             )

#         return text
#     # ========================================================
#     # TRANSLATE STRUCTURED ANSWER
#     # ========================================================

#     def translate_answer(
#         self,
#         answer,
#         language
#     ):

#         # ----------------------------------------------------
#         # English output requested
#         # ----------------------------------------------------

#         if language == "en":
#             return answer

#         # ----------------------------------------------------
#         # Unsupported language
#         # ----------------------------------------------------

#         if language != "hi":
#             return answer

#         if not isinstance(answer, dict):
#             return answer

#         translated_answer = {

#             "type": answer.get(
#                 "type",
#                 "mixed"
#             ),

#             "content": []
#         }

#         # ====================================================
#         # CONTENT
#         # ====================================================

#         for item in answer.get(
#             "content",
#             []
#         ):

#             if not isinstance(item, dict):
#                 continue

#             item_type = item.get("type")

#             # ------------------------------------------------
#             # Paragraph / Heading / Warning
#             # ------------------------------------------------

#             if item_type in {
#                 "paragraph",
#                 "heading",
#                 "warning"
#             }:

#                 translated_answer[
#                     "content"
#                 ].append({

#                     "type": item_type,

#                     "text":
#                         self.translate_to_hindi(
#                             item.get(
#                                 "text",
#                                 ""
#                             )
#                         )
#                 })

#             # ------------------------------------------------
#             # Bullet / Numbered List
#             # ------------------------------------------------

#             elif item_type in {
#                 "bullet_list",
#                 "numbered_list"
#             }:

#                 items = item.get(
#                     "items",
#                     []
#                 )

#                 translated_items = []

#                 for text in items:

#                     translated_items.append(
#                         self.translate_to_hindi(
#                             text
#                         )
#                     )

#                 translated_answer[
#                     "content"
#                 ].append({

#                     "type": item_type,

#                     "items": translated_items
#                 })

#             # ------------------------------------------------
#             # Unknown content type
#             # ------------------------------------------------

#             else:

#                 translated_answer[
#                     "content"
#                 ].append(item)

#         return translated_answer






























































# from deep_translator import GoogleTranslator


# class Translator:

#     def __init__(self):

#         print("Loading translator: deep-translator")

#         self.hindi_to_english = GoogleTranslator(
#             source="hi",
#             target="en"
#         )

#         self.english_to_hindi = GoogleTranslator(
#             source="en",
#             target="hi"
#         )

#         print("Translator ready.")

#     # ========================================================
#     # HINDI → ENGLISH
#     # ========================================================

#     def translate_to_english(self, text):

#         if not text or not text.strip():
#             return text

#         try:

#             result = self.hindi_to_english.translate(
#                 text.strip()
#             )

#             if result and result.strip():
#                 return result.strip()

#         except Exception as e:

#             print(
#                 f"Translation error (HI → EN): {e}"
#             )

#         return text

#     # ========================================================
#     # ENGLISH → HINDI
#     # ========================================================

#     def translate_to_hindi(self, text):

#         if not text or not text.strip():
#             return text

#         text = text.strip()

#         try:

#             result = self.english_to_hindi.translate(text)

#             if result and result.strip():
#                 return result.strip()

#         except Exception:
#             pass

#         # ----------------------------------------------------
#         # Fallback: sentence-by-sentence translation
#         # ----------------------------------------------------

#         try:

#             sentences = [
#                 s.strip()
#                 for s in text.replace("!", ".")
#                               .replace("?", ".")
#                               .split(".")
#                 if s.strip()
#             ]

#             translated_parts = []

#             for sentence in sentences:

#                 try:

#                     result = self.english_to_hindi.translate(
#                         sentence
#                     )

#                     if result and result.strip():
#                         translated_parts.append(
#                             result.strip()
#                         )
#                     else:
#                         translated_parts.append(sentence)

#                 except Exception:
#                     translated_parts.append(sentence)

#             if translated_parts:
#                 return " ".join(translated_parts)

#         except Exception as e:

#             print(
#                 f"Fallback translation error (EN → HI): {e}"
#             )

#         # ----------------------------------------------------
#         # Final fallback
#         # ----------------------------------------------------

#         return text

#     # ========================================================
#     # TRANSLATE STRUCTURED ANSWER
#     # ========================================================

#     def translate_answer(
#         self,
#         answer,
#         language
#     ):

#         # ----------------------------------------------------
#         # English output requested
#         # ----------------------------------------------------

#         if language == "en":
#             return answer

#         # ----------------------------------------------------
#         # Unsupported language
#         # ----------------------------------------------------

#         if language != "hi":
#             return answer

#         if not isinstance(answer, dict):
#             return answer

#         translated_answer = {

#             "type": answer.get(
#                 "type",
#                 "mixed"
#             ),

#             "content": []
#         }

#         # ====================================================
#         # CONTENT
#         # ====================================================

#         for item in answer.get(
#             "content",
#             []
#         ):

#             if not isinstance(item, dict):
#                 continue

#             item_type = item.get("type")

#             # ------------------------------------------------
#             # Paragraph / Heading / Warning
#             # ------------------------------------------------

#             if item_type in {
#                 "paragraph",
#                 "heading",
#                 "warning"
#             }:

#                 translated_answer[
#                     "content"
#                 ].append({

#                     "type": item_type,

#                     "text":
#                         self.translate_to_hindi(
#                             item.get(
#                                 "text",
#                                 ""
#                             )
#                         )
#                 })

#             # ------------------------------------------------
#             # Bullet / Numbered List
#             # ------------------------------------------------

#             elif item_type in {
#                 "bullet_list",
#                 "numbered_list"
#             }:

#                 items = item.get(
#                     "items",
#                     []
#                 )

#                 translated_items = []

#                 for text in items:

#                     translated_items.append(
#                         self.translate_to_hindi(
#                             text
#                         )
#                     )

#                 translated_answer[
#                     "content"
#                 ].append({

#                     "type": item_type,

#                     "items": translated_items
#                 })

#             # ------------------------------------------------
#             # Unknown content type
#             # ------------------------------------------------

#             else:

#                 translated_answer[
#                     "content"
#                 ].append(item)

#         return translated_answer









import time
# from deep_translator import GoogleTranslator
from deep_translator import MyMemoryTranslator

class Translator:

    def __init__(self):

        print("Loading translator: deep-translator")

        self.hindi_to_english = MyMemoryTranslator(
            source="hindi",
            target="english"
        )

        self.english_to_hindi = MyMemoryTranslator(
            source="english",
            target="hindi"
        )

        # Small delay between Google requests
        self.request_delay = 0.3

        # Avoid translating the same text repeatedly
        self.translation_cache = {}

        print("Translator ready.")

    # ========================================================
    # HINDI → ENGLISH
    # ========================================================

    def translate_to_english(self, text):

        if not text or not text.strip():
            return text

        text = text.strip()

        # Cache
        cache_key = ("hi-en", text)

        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        try:

            result = self.hindi_to_english.translate(text)

            if result and result.strip():

                result = result.strip()

                self.translation_cache[cache_key] = result

                return result

        except Exception as e:

            print(
                f"Translation error (HI → EN): {e}"
            )

        # Final fallback
        return text

    # ========================================================
    # ENGLISH → HINDI
    # ========================================================

    def translate_to_hindi(self, text):

        if not text or not text.strip():
            return text

        text = text.strip()

        # ----------------------------------------------------
        # Cache
        # ----------------------------------------------------

        cache_key = ("en-hi", text)

        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]

        # ----------------------------------------------------
        # First attempt: translate complete text
        # ----------------------------------------------------

        try:

            result = self.english_to_hindi.translate(text)

            if result and result.strip():

                result = result.strip()

                # Google sometimes returns the original text
                # instead of translating it.
                if result.lower() != text.lower():

                    self.translation_cache[cache_key] = result

                    return result

        except Exception as e:

            print(
                f"Translation error (EN → HI): {e}"
            )

        # ----------------------------------------------------
        # Fallback: split into smaller chunks
        # ----------------------------------------------------

        print(
            "Trying smaller translation chunks..."
        )

        try:

            chunks = self._split_text(text)

            translated_parts = []

            for chunk in chunks:

                if not chunk.strip():
                    continue

                chunk_key = ("en-hi", chunk.strip())

                # Use cached result if available
                if chunk_key in self.translation_cache:

                    translated_parts.append(
                        self.translation_cache[chunk_key]
                    )

                    continue

                try:

                    time.sleep(
                        self.request_delay
                    )

                    result = self.english_to_hindi.translate(
                        chunk
                    )

                    if result and result.strip():

                        result = result.strip()

                        # Check whether translation actually changed
                        # the text.
                        if result.lower() != chunk.lower():

                            self.translation_cache[
                                chunk_key
                            ] = result

                            translated_parts.append(result)

                        else:

                            translated_parts.append(chunk)

                    else:

                        translated_parts.append(chunk)

                except Exception as e:

                    print(
                        f"Chunk translation error: {e}"
                    )

                    translated_parts.append(chunk)

            if translated_parts:

                final_result = " ".join(
                    translated_parts
                )

                self.translation_cache[
                    cache_key
                ] = final_result

                return final_result

        except Exception as e:

            print(
                f"Fallback translation error (EN → HI): {e}"
            )

        # ----------------------------------------------------
        # Final fallback
        # ----------------------------------------------------

        return text

    # ========================================================
    # SPLIT TEXT
    # ========================================================

    def _split_text(
        self,
        text,
        max_length=400
    ):

        """
        Split long English text into manageable chunks.

        Preference:
        1. Paragraphs
        2. Sentences
        3. Character limit
        """

        paragraphs = [
            p.strip()
            for p in text.split("\n")
            if p.strip()
        ]

        if not paragraphs:
            return [text]

        chunks = []

        for paragraph in paragraphs:

            # Small paragraph → keep as one chunk
            if len(paragraph) <= max_length:

                chunks.append(paragraph)

                continue

            # ------------------------------------------------
            # Large paragraph → split by sentences
            # ------------------------------------------------

            sentences = [
                s.strip()
                for s in paragraph.replace(
                    "!", "."
                ).replace(
                    "?", "."
                ).split(".")
                if s.strip()
            ]

            current_chunk = ""

            for sentence in sentences:

                if not current_chunk:

                    current_chunk = sentence

                elif len(
                    current_chunk
                ) + len(sentence) + 1 <= max_length:

                    current_chunk += (
                        ". " + sentence
                    )

                else:

                    chunks.append(
                        current_chunk
                    )

                    current_chunk = sentence

            if current_chunk:

                chunks.append(
                    current_chunk
                )

        return chunks

    # ========================================================
    # TRANSLATE STRUCTURED ANSWER
    # ========================================================

    def translate_answer(
        self,
        answer,
        language
    ):

        # ----------------------------------------------------
        # English output requested
        # ----------------------------------------------------

        if language == "en":
            return answer

        # ----------------------------------------------------
        # Unsupported language
        # ----------------------------------------------------

        if language != "hi":
            return answer

        if not isinstance(answer, dict):
            return answer

        translated_answer = {

            "type": answer.get(
                "type",
                "mixed"
            ),

            "content": []
        }

        # ====================================================
        # CONTENT
        # ====================================================

        for item in answer.get(
            "content",
            []
        ):

            if not isinstance(item, dict):
                continue

            item_type = item.get("type")

            # ------------------------------------------------
            # Paragraph / Heading / Warning
            # ------------------------------------------------

            if item_type in {
                "paragraph",
                "heading",
                "warning"
            }:

                translated_answer[
                    "content"
                ].append({

                    "type": item_type,

                    "text":
                        self.translate_to_hindi(
                            item.get(
                                "text",
                                ""
                            )
                        )
                })

            # ------------------------------------------------
            # Bullet / Numbered List
            # ------------------------------------------------

            elif item_type in {
                "bullet_list",
                "numbered_list"
            }:

                items = item.get(
                    "items",
                    []
                )

                translated_items = []

                for text in items:

                    translated_items.append(
                        self.translate_to_hindi(
                            text
                        )
                    )

                translated_answer[
                    "content"
                ].append({

                    "type": item_type,

                    "items": translated_items
                })

            # ------------------------------------------------
            # Unknown content type
            # ------------------------------------------------

            else:

                translated_answer[
                    "content"
                ].append(item)

        return translated_answer

    

    def is_hindi(self, text):
      return any(
        "\u0900" <= char <= "\u097F"
        for char in text
      )