import torch
import torch.nn as nn

class LSTMForecaster(nn.Module):

    def __init__(self,input_size=12,hidden_size=64,num_layers=2,output_size=5,dropout=0.2):
        super().__init__()

        self.lstm=nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,        
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout
        )

        self.fc=nn.Linear(hidden_size,output_size)

    def forward(self,x):
        lstm_out,_=self.lstm(x)
        last_hidden=lstm_out[:,-1,:]
        output=self.fc(last_hidden)
        return output