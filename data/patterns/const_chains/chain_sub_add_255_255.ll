define i32 @chain_sub_add_255_255(i32 %x) {
entry:
  %tmp = sub i32 %x, 255
  %result = add i32 %tmp, 255
  ret i32 %result
}
