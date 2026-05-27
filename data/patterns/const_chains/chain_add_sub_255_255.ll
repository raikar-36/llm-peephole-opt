define i32 @chain_add_sub_255_255(i32 %x) {
entry:
  %tmp = add i32 %x, 255
  %result = sub i32 %tmp, 255
  ret i32 %result
}
