define i32 @chain_add_sub_4_4(i32 %x) {
entry:
  %tmp = add i32 %x, 4
  %result = sub i32 %tmp, 4
  ret i32 %result
}
