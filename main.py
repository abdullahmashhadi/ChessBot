def CreateGraphicalBoard():
    for row in range (8):
        for column in range(8):
            is_light_square=((column+row)%2)==0
            square_colour= "light" if is_light_square else "dark"
            print(f"grid position {row, column} is: {square_colour}")
            
    
CreateGraphicalBoard()

