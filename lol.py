def reversewords(s:str):
    i = 0
    for char in range(0, len(s)):
        print(char)
        if s[char]== " ":
            temp = s[i:char]
            i = char
            print("temp",temp)


call = reversewords("blue is sky the")
print(call)
