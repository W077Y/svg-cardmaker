python generate_cards.py --input .\card-db
python collect_and_print.py `
  --cards ".\out_cards" `
  --add "Potion_of_Healing=10" `
  --add "Potion_of_Greater_Healing=5" `
  --add "Potion_of_Superior_Healing=3" `
  --add "Potion_of_Supreme_Healing=1" `
  --out "cards_print.pdf" `
  --crop 