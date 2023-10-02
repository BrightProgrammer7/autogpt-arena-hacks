from transformers import AutoModelForCausalLM, AutoTokenizer      
import gradio as gr      
import torch      
    
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")    
tokenizer.padding_side = 'left'      
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")     
    
class ChatBot:      
    def __init__(self):      
        self.history = []      
    
    def predict(self, input):            
        new_user_input_ids = tokenizer.encode(input + tokenizer.eos_token, return_tensors="pt")            
        flat_history = [item for sublist in self.history for item in sublist]       
        flat_history_tensor = torch.tensor(flat_history).unsqueeze(dim=0)  # convert list to 2-D tensor    
        bot_input_ids = torch.cat([flat_history_tensor, new_user_input_ids], dim=-1) if self.history else new_user_input_ids            
        chat_history_ids = model.generate(bot_input_ids, max_length=2000, pad_token_id=tokenizer.eos_token_id)            
        self.history.append(chat_history_ids[:, bot_input_ids.shape[-1]:].tolist()[0])            
        response = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)     
        return response      
  
bot = ChatBot() 
  
title = "👋🏻Welcome to Tonic's EZ Chat🚀"    
description = "You can use this Space to test out the current model (DialoGPT-medium) or duplicate this Space and use it for any other model on 🤗HuggingFace. Join me on [Discord](https://discord.gg/fpEPNZGsbt) to build together."    
examples = [["How are you?"]]    
  
iface = gr.Interface(    
    fn=bot.predict,    
    title=title,    
    description=description,    
    examples=examples,    
    inputs="text",    
    outputs="text", 
    theme="ParityError/Anime"
)    
  
iface.launch()  
